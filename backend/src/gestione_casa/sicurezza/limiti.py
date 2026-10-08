# SPDX-License-Identifier: AGPL-3.0-or-later
"""Limitazione dei tentativi falliti (M1-05).

Per ogni operazione sensibile (login, recupero password, accettazione inviti) si contano i
fallimenti degli ultimi ``FINESTRA`` minuti, separatamente per indirizzo IP e per email.
Al raggiungimento di ``MASSIMO`` fallimenti per una delle chiavi, l'operazione è bloccata
finché il fallimento più vecchio non esce dalla finestra. Contatori in PostgreSQL: nessun
servizio aggiuntivo.

Dietro Caddy l'indirizzo del client arriva da ``X-Forwarded-For`` (uvicorn con
``--proxy-headers``).
"""

import enum
import math
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestione_casa.errors import AppError
from gestione_casa.models import TentativoFallito

FINESTRA = timedelta(minutes=15)
MASSIMO = 5
CONSERVAZIONE = timedelta(days=1)


class Ambito(enum.StrEnum):
    LOGIN = "login"
    RECUPERO_PASSWORD = "recupero_password"  # noqa: S105 (nome di un ambito, non una password)
    INVITO = "invito"
    PRIMO_AVVIO = "primo_avvio"


def chiavi(request: Request, email: str | None = None) -> list[str]:
    """Chiavi da limitare: indirizzo del client ed eventuale email (già normalizzata)."""
    risultato = [f"ip:{request.client.host if request.client else 'sconosciuto'}"]
    if email:
        risultato.append(f"email:{email}")
    return risultato


async def verifica_limite(db: AsyncSession, ambito: Ambito, elenco: list[str]) -> None:
    """Solleva ``auth.too_many_attempts`` (429) se una chiave ha superato il limite."""
    adesso = datetime.now(UTC)
    righe = (
        await db.execute(
            select(TentativoFallito.chiave, func.count(), func.min(TentativoFallito.avvenuto_il))
            .where(
                TentativoFallito.ambito == ambito.value,
                TentativoFallito.chiave.in_(elenco),
                TentativoFallito.avvenuto_il > adesso - FINESTRA,
            )
            .group_by(TentativoFallito.chiave)
        )
    ).all()
    bloccate = [primo for _, numero, primo in righe if numero >= MASSIMO]
    if bloccate:
        sblocco = min(bloccate) + FINESTRA
        attesa = max(1, math.ceil((sblocco - adesso).total_seconds()))
        raise AppError(
            "auth.too_many_attempts",
            status_code=429,
            headers={"Retry-After": str(attesa)},
            retry_after=attesa,
            minutes=math.ceil(attesa / 60),
        )


async def registra_fallimento(db: AsyncSession, ambito: Ambito, elenco: list[str]) -> None:
    adesso = datetime.now(UTC)
    db.add_all(
        [TentativoFallito(ambito=ambito.value, chiave=c, avvenuto_il=adesso) for c in elenco]
    )
    await db.execute(
        delete(TentativoFallito).where(TentativoFallito.avvenuto_il < adesso - CONSERVAZIONE)
    )


async def azzera(db: AsyncSession, ambito: Ambito, elenco: list[str]) -> None:
    """Dopo un'operazione riuscita i fallimenti precedenti non contano più."""
    await db.execute(
        delete(TentativoFallito).where(
            TentativoFallito.ambito == ambito.value, TentativoFallito.chiave.in_(elenco)
        )
    )
