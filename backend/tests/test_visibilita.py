# SPDX-License-Identifier: AGPL-3.0-or-later
"""Filtro di visibilità unico (M1-13): nessuna query dell'ORM vede o modifica privati altrui."""

from collections.abc import Iterator
from typing import NamedTuple

import pytest
from sqlalchemy import String, create_engine, delete, func, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, Session, aliased, mapped_column

from gestione_casa.config import get_settings
from gestione_casa.models import Base, Utente
from gestione_casa.models.base import ContenutoMixin, Visibilita
from gestione_casa.visibilita import imposta_sistema, imposta_utente


class ElementoProva(ContenutoMixin, Base):
    """Entità di contenuto usata solo nei test (tabella con prefisso "prova_")."""

    __tablename__ = "prova_elemento"

    id: Mapped[int] = mapped_column(primary_key=True)
    titolo: Mapped[str] = mapped_column(String(50))


class Dati(NamedTuple):
    engine: Engine
    camillo: int
    aurora: int
    privato_camillo: int
    condiviso_camillo: int
    privato_aurora: int


@pytest.fixture
def dati(database: None) -> Iterator[Dati]:
    engine = create_engine(get_settings().url_database())
    tabella = ElementoProva.__table__
    tabella.create(engine)  # type: ignore[attr-defined]
    try:
        with Session(engine) as s:
            imposta_sistema(s)
            camillo = Utente(nome="Camillo", email="c@example.com", hash_password="x")
            aurora = Utente(nome="Aurora", email="a@example.com", hash_password="x")
            s.add_all([camillo, aurora])
            s.flush()
            elementi = [
                ElementoProva(
                    titolo="privato C", proprietario_id=camillo.id, visibilita=Visibilita.PRIVATO
                ),
                ElementoProva(titolo="condiviso C", proprietario_id=camillo.id),
                ElementoProva(
                    titolo="privato A", proprietario_id=aurora.id, visibilita=Visibilita.PRIVATO
                ),
            ]
            s.add_all(elementi)
            s.commit()
            yield Dati(engine, camillo.id, aurora.id, *(e.id for e in elementi))
    finally:
        tabella.drop(engine)  # type: ignore[attr-defined]
        engine.dispose()


def _titoli(s: Session) -> set[str]:
    return set(s.scalars(select(ElementoProva.titolo)))


def test_ognuno_vede_condivisi_e_propri_privati(dati: Dati) -> None:
    with Session(dati.engine) as s:
        imposta_utente(s, dati.camillo)
        assert _titoli(s) == {"privato C", "condiviso C"}
    with Session(dati.engine) as s:
        imposta_utente(s, dati.aurora)
        assert _titoli(s) == {"condiviso C", "privato A"}


def test_lettura_diretta_di_un_privato_altrui(dati: Dati) -> None:
    with Session(dati.engine) as s:
        imposta_utente(s, dati.camillo)
        assert s.get(ElementoProva, dati.privato_aurora) is None
        assert s.get(ElementoProva, dati.condiviso_camillo) is not None


def test_conteggi_alias_e_join(dati: Dati) -> None:
    with Session(dati.engine) as s:
        imposta_utente(s, dati.camillo)
        assert s.scalar(select(func.count()).select_from(ElementoProva)) == 2
        alias = aliased(ElementoProva)
        assert len(s.scalars(select(alias.titolo)).all()) == 2
        righe = s.execute(
            select(Utente.nome, ElementoProva.titolo).join(
                ElementoProva, ElementoProva.proprietario_id == Utente.id
            )
        ).all()
        assert ("Aurora", "privato A") not in righe


def test_modifica_ed_eliminazione_rispettano_il_filtro(dati: Dati) -> None:
    with Session(dati.engine) as s:
        imposta_utente(s, dati.camillo)
        modificati = s.execute(update(ElementoProva).values(titolo="modificato"))
        eliminati = s.execute(delete(ElementoProva).where(ElementoProva.id == dati.privato_aurora))
        s.commit()
        assert modificati.rowcount == 2  # type: ignore[attr-defined]
        assert eliminati.rowcount == 0  # type: ignore[attr-defined]
    with Session(dati.engine) as s:
        imposta_sistema(s)
        assert _titoli(s) == {"modificato", "privato A"}


def test_senza_contesto_non_si_vede_nulla(dati: Dati) -> None:
    with Session(dati.engine) as s:
        assert _titoli(s) == set()


def test_contesto_di_sistema_vede_tutto(dati: Dati) -> None:
    with Session(dati.engine) as s:
        imposta_sistema(s)
        assert len(_titoli(s)) == 3


def test_cambio_di_utente_nella_stessa_sessione(dati: Dati) -> None:
    with Session(dati.engine) as s:
        imposta_utente(s, dati.camillo)
        assert "privato C" in _titoli(s)
        imposta_utente(s, dati.aurora)
        s.expunge_all()
        assert _titoli(s) == {"condiviso C", "privato A"}


def test_altre_entita_non_filtrate(dati: Dati) -> None:
    with Session(dati.engine) as s:
        assert len(s.scalars(select(Utente)).all()) == 2


@pytest.mark.anyio
async def test_sessione_asincrona(dati: Dati) -> None:
    engine = create_async_engine(get_settings().url_database())
    try:
        async with AsyncSession(engine) as s:
            imposta_utente(s, dati.aurora)
            titoli = set((await s.scalars(select(ElementoProva.titolo))).all())
            assert titoli == {"condiviso C", "privato A"}
    finally:
        await engine.dispose()


def test_visibilita_non_valida_rifiutata_dal_database(dati: Dati) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    with Session(dati.engine) as s, pytest.raises(IntegrityError):
        s.execute(
            text(
                "INSERT INTO prova_elemento (titolo, proprietario_id, visibilita) "
                "VALUES ('x', :p, 'pubblico')"
            ),
            {"p": dati.camillo},
        )


def test_cache_delle_query_non_mescola_i_contesti(dati: Dati) -> None:
    """La stessa query eseguita in contesti diversi non riusa il criterio sbagliato."""
    attesi = [
        (dati.camillo, {"privato C", "condiviso C"}),
        (None, set()),
        (dati.aurora, {"condiviso C", "privato A"}),
        (None, set()),
        (dati.camillo, {"privato C", "condiviso C"}),
    ]
    for utente, titoli in attesi:
        with Session(dati.engine) as s:
            if utente is not None:
                imposta_utente(s, utente)
            assert _titoli(s) == titoli, f"contesto {utente}"
