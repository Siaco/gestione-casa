# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sessioni salvate nel database (paragrafo 9, M1-03).

Il token sta solo nel cookie del browser; nel database c'è la sua impronta. Una sessione dura
``sessione_durata_giorni`` e si rinnova con l'uso (al massimo una scrittura ogni ora).
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestione_casa.config import get_settings
from gestione_casa.models import Sessione, Utente
from gestione_casa.sicurezza.token import genera_token, impronta

INTERVALLO_RINNOVO = timedelta(hours=1)
LUNGHEZZA_DISPOSITIVO = 255


def adesso() -> datetime:
    return datetime.now(UTC)


def _durata() -> timedelta:
    return timedelta(days=get_settings().sessione_durata_giorni)


@dataclass(frozen=True, slots=True)
class SessioneAttiva:
    sessione: Sessione
    utente: Utente


async def crea_sessione(db: AsyncSession, utente: Utente, dispositivo: str | None) -> str:
    """Crea una sessione e restituisce il token da mettere nel cookie (mai salvato)."""
    generato = genera_token()
    ora = adesso()
    db.add(
        Sessione(
            utente_id=utente.id,
            impronta_token=generato.impronta,
            creata_il=ora,
            ultimo_uso=ora,
            scade_il=ora + _durata(),
            dispositivo=(dispositivo or "")[:LUNGHEZZA_DISPOSITIVO] or None,
        )
    )
    await db.flush()
    return generato.token


async def trova_sessione(db: AsyncSession, token: str) -> SessioneAttiva | None:
    """Sessione valida per il token, rinnovata se serve; ``None`` se assente o scaduta."""
    riga = (
        await db.execute(
            select(Sessione, Utente)
            .join(Utente, Utente.id == Sessione.utente_id)
            .where(Sessione.impronta_token == impronta(token))
        )
    ).first()
    if riga is None:
        return None
    sessione, utente = riga
    ora = adesso()
    if sessione.scade_il <= ora or not utente.attivo:
        await db.delete(sessione)
        await db.commit()
        return None
    if ora - sessione.ultimo_uso >= INTERVALLO_RINNOVO:
        sessione.ultimo_uso = ora
        sessione.scade_il = ora + _durata()
        await db.commit()
    return SessioneAttiva(sessione=sessione, utente=utente)


async def elimina_sessione(db: AsyncSession, token: str) -> None:
    await db.execute(delete(Sessione).where(Sessione.impronta_token == impronta(token)))


async def elimina_sessioni_utente(db: AsyncSession, utente_id: int) -> None:
    """Usata al cambio o al recupero della password: tutti i dispositivi escono."""
    await db.execute(delete(Sessione).where(Sessione.utente_id == utente_id))


async def elimina_sessioni_scadute(db: AsyncSession) -> int:
    risultato = await db.execute(delete(Sessione).where(Sessione.scade_il <= adesso()))
    return int(risultato.rowcount or 0)  # type: ignore[attr-defined]
