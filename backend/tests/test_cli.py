# SPDX-License-Identifier: AGPL-3.0-or-later
"""Comando di emergenza per reimpostare la password (M1-09)."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from gestione_casa import cli
from gestione_casa.config import get_settings
from gestione_casa.models import Sessione, Utente
from gestione_casa.sicurezza.password import calcola_hash, verifica_password
from gestione_casa.sicurezza.token import genera_token

pytestmark = pytest.mark.anyio


@pytest.fixture
def engine(database: None) -> Iterator[Engine]:
    e = create_engine(get_settings().url_database())
    with Session(e) as s:
        u = Utente(
            nome="Aurora",
            email="Aurora@example.com",
            hash_password=calcola_hash("vecchia password"),
        )
        s.add(u)
        s.flush()
        s.add(
            Sessione(
                utente_id=u.id,
                impronta_token=genera_token().impronta,
                scade_il=datetime.now(UTC) + timedelta(days=1),
            )
        )
        s.commit()
    yield e
    e.dispose()


def _risposte(*valori: str) -> Callable[[str], str]:
    iteratore = iter(valori)
    return lambda _prompt: next(iteratore)


def _stato(engine: Engine) -> tuple[str, int]:
    with Session(engine) as s:
        hash_ = s.scalar(select(Utente.hash_password)) or ""
        sessioni = s.scalar(select(func.count()).select_from(Sessione)) or 0
    return hash_, sessioni


async def test_password_reimpostata_e_sessioni_chiuse(engine: Engine) -> None:
    riuscito, messaggio = await cli.reimposta_password(
        "aurora@EXAMPLE.com", _risposte("nuova password lunga", "nuova password lunga")
    )
    assert riuscito, messaggio
    hash_, sessioni = _stato(engine)
    assert verifica_password(hash_, "nuova password lunga").valida
    assert sessioni == 0


@pytest.mark.parametrize(
    ("email", "risposte", "atteso"),
    [
        ("nessuno@example.com", (), "Nessun utente"),
        (
            "aurora@example.com",
            ("nuova password lunga", "diversa password lunga"),
            "non coincidono",
        ),
        ("aurora@example.com", ("corta", "corta"), "almeno 12 caratteri"),
    ],
)
async def test_nessuna_modifica_se_non_valida(
    engine: Engine, email: str, risposte: tuple[str, ...], atteso: str
) -> None:
    prima = _stato(engine)
    riuscito, messaggio = await cli.reimposta_password(email, _risposte(*risposte))
    assert not riuscito and atteso in messaggio
    assert _stato(engine) == prima


def test_comando_da_terminale(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "getpass.getpass", _risposte("nuova password lunga", "nuova password lunga")
    )
    assert cli.main(["reimposta-password", "--email", "aurora@example.com"]) == 0
    assert cli.main(["reimposta-password", "--email", "nessuno@example.com"]) == 1
