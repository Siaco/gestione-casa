# SPDX-License-Identifier: AGPL-3.0-or-later
"""Primo avvio guidato (M1-06)."""

import logging
import re
from collections.abc import Iterator

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from gestione_casa.auth import primo_avvio
from gestione_casa.config import get_settings
from gestione_casa.models import Sessione, Utente
from gestione_casa.sicurezza.limiti import MASSIMO

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def codice_nuovo() -> Iterator[None]:
    primo_avvio.consuma_codice()
    yield
    primo_avvio.consuma_codice()


@pytest.fixture
def engine(database: None) -> Iterator[Engine]:
    e = create_engine(get_settings().url_database())
    yield e
    e.dispose()


def _utenti(engine: Engine) -> int:
    with Session(engine) as s:
        return int(s.scalar(select(func.count()).select_from(Utente)) or 0)


async def _codice_dai_log(client: AsyncClient, caplog: pytest.LogCaptureFixture) -> str:
    with caplog.at_level(logging.WARNING, logger="gestione_casa.primo_avvio"):
        r = await client.get("/api/setup")
    assert r.json() == {"necessaria": True}
    trovato = re.search(r"codice ([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})", caplog.text)
    assert trovato, caplog.text
    return trovato.group(1)


async def _crea(client: AsyncClient, codice: str, **altri: str) -> Response:
    dati = {
        "codice": codice,
        "nome": "Camillo",
        "email": " Camillo@Example.com ",
        "password": "una password lunga",
        **altri,
    }
    return await client.post("/api/setup", json=dati)


async def test_primo_utente_creato_e_collegato(
    client: AsyncClient, engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    codice = await _codice_dai_log(client, caplog)
    r = await _crea(client, codice.lower().replace("-", " "))  # tollerante su formato
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["utente"]["email"] == "camillo@example.com"
    assert len(corpo["csrf_token"]) == 64
    assert codice not in r.text
    assert (await client.get("/api/auth/me")).status_code == 200
    assert (await client.get("/api/setup")).json() == {"necessaria": False}
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(Sessione)) == 1


async def test_codice_mai_nelle_risposte(
    client: AsyncClient, engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    codice = await _codice_dai_log(client, caplog)
    r = await client.get("/api/setup")
    assert codice not in r.text and codice.replace("-", "") not in r.text


async def test_codice_errato(
    client: AsyncClient, engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    await _codice_dai_log(client, caplog)
    r = await _crea(client, "AAAA-BBBB-CCCC")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "setup.invalid_code"
    assert _utenti(engine) == 0


async def test_disattivato_dopo_il_primo_utente(
    client: AsyncClient, engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    codice = await _codice_dai_log(client, caplog)
    assert (await _crea(client, codice)).status_code == 201
    r = await _crea(client, codice, email="altro@example.com")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "setup.already_done"
    assert _utenti(engine) == 1


async def test_senza_codice_generato_nessun_accesso(client: AsyncClient, engine: Engine) -> None:
    r = await _crea(client, "")
    assert r.status_code == 422  # codice vuoto
    r = await _crea(client, "AAAA-BBBB-CCCC")
    assert r.status_code == 403


@pytest.mark.parametrize(
    ("campi", "codice_errore"),
    [
        ({"password": "corta"}, "auth.password_too_short"),
        ({"email": "non-una-email"}, "auth.email_invalid"),
        ({"password": "camillo@example.com"}, "auth.password_equals_email"),
    ],
)
async def test_dati_non_validi(
    client: AsyncClient,
    engine: Engine,
    caplog: pytest.LogCaptureFixture,
    campi: dict[str, str],
    codice_errore: str,
) -> None:
    codice = await _codice_dai_log(client, caplog)
    r = await _crea(client, codice, **campi)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == codice_errore
    assert _utenti(engine) == 0
    assert (await _crea(client, codice)).status_code == 201  # codice ancora valido


async def test_tentativi_limitati(
    client: AsyncClient, engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    codice = await _codice_dai_log(client, caplog)
    for _ in range(MASSIMO):
        await _crea(client, "AAAA-BBBB-CCCC")
    assert (await _crea(client, codice)).status_code == 429
