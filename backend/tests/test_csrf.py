# SPDX-License-Identifier: AGPL-3.0-or-later
"""Protezione CSRF: controllo dell'origine e token legato alla sessione (M1-04)."""

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from gestione_casa.auth.dipendenze import Db, UtenteCorrente
from gestione_casa.config import get_settings
from gestione_casa.db import get_engine
from gestione_casa.main import create_app
from gestione_casa.models import Utente
from gestione_casa.sicurezza.csrf import origine_ammessa, token_csrf, token_valido
from gestione_casa.sicurezza.password import calcola_hash
from gestione_casa.visibilita import CHIAVE_UTENTE

pytestmark = pytest.mark.anyio
PASSWORD = "una password lunga"


@pytest.mark.parametrize(
    ("origin", "referer", "host", "ammessa"),
    [
        (None, None, "zeus.fritz.box", True),  # client non browser
        ("http://zeus.fritz.box", None, "zeus.fritz.box", True),
        ("http://ZEUS.fritz.box", None, "zeus.fritz.box", True),
        ("http://zeus.fritz.box:8080", None, "zeus.fritz.box:8080", True),
        (None, "http://zeus.fritz.box/pagina", "zeus.fritz.box", True),
        ("https://sito-malevolo.example", None, "zeus.fritz.box", False),
        (None, "https://sito-malevolo.example/x", "zeus.fritz.box", False),
        ("http://zeus.fritz.box:9999", None, "zeus.fritz.box", False),
        ("null", None, "zeus.fritz.box", False),
        ("http://zeus.fritz.box", None, None, False),
    ],
)
def test_origine(origin: str | None, referer: str | None, host: str | None, ammessa: bool) -> None:
    assert origine_ammessa(origin, referer, host) is ammessa


def test_token_legato_alla_sessione() -> None:
    assert token_valido("sessione-a", token_csrf("sessione-a"))
    assert not token_valido("sessione-b", token_csrf("sessione-a"))
    assert not token_valido("sessione-a", None)
    assert not token_valido("sessione-a", "")


@pytest.fixture
def engine(database: None) -> Iterator[Engine]:
    e = create_engine(get_settings().url_database())
    with Session(e) as s:
        s.add(Utente(nome="Camillo", email="c@example.com", hash_password=calcola_hash(PASSWORD)))
        s.commit()
    yield e
    e.dispose()


def _app_con_endpoint_di_prova() -> FastAPI:
    app = create_app()

    @app.post("/api/prova")
    async def prova(utente: UtenteCorrente, db: Db) -> dict[str, object]:
        return {"utente": utente.nome, "contesto": db.sync_session.info.get(CHIAVE_UTENTE)}

    @app.get("/api/prova")
    async def prova_lettura(utente: UtenteCorrente) -> dict[str, str]:
        return {"utente": utente.nome}

    return app


@pytest.fixture
async def client(engine: Engine) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=_app_con_endpoint_di_prova())
    async with AsyncClient(transport=transport, base_url="http://zeus.fritz.box") as c:
        yield c
    await get_engine().dispose()


async def _accedi(client: AsyncClient) -> str:
    r = await client.post("/api/auth/login", json={"email": "c@example.com", "password": PASSWORD})
    assert r.status_code == 200
    return str(r.json()["csrf_token"])


async def test_modifica_con_token_e_contesto_di_visibilita(client: AsyncClient) -> None:
    token = await _accedi(client)
    r = await client.post("/api/prova", headers={"X-CSRF-Token": token})
    assert r.status_code == 200
    assert r.json() == {"utente": "Camillo", "contesto": 1}


@pytest.mark.parametrize("intestazioni", [{}, {"X-CSRF-Token": "sbagliato"}])
async def test_modifica_senza_token_valido(
    client: AsyncClient, intestazioni: dict[str, str]
) -> None:
    await _accedi(client)
    r = await client.post("/api/prova", headers=intestazioni)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "auth.csrf_invalid"


async def test_lettura_senza_token(client: AsyncClient) -> None:
    await _accedi(client)
    assert (await client.get("/api/prova")).status_code == 200


async def test_origine_estranea_respinta_anche_con_token(client: AsyncClient) -> None:
    token = await _accedi(client)
    r = await client.post(
        "/api/prova",
        headers={"X-CSRF-Token": token, "Origin": "https://sito-malevolo.example"},
    )
    assert r.status_code == 403


async def test_login_da_origine_estranea_respinto(client: AsyncClient) -> None:
    r = await client.post(
        "/api/auth/login",
        json={"email": "c@example.com", "password": PASSWORD},
        headers={"Origin": "https://sito-malevolo.example"},
    )
    assert r.status_code == 403
    assert "set-cookie" not in r.headers


async def test_login_dalla_stessa_origine(client: AsyncClient) -> None:
    r = await client.post(
        "/api/auth/login",
        json={"email": "c@example.com", "password": PASSWORD},
        headers={"Origin": "http://zeus.fritz.box"},
    )
    assert r.status_code == 200


async def test_token_cambia_con_la_sessione(client: AsyncClient) -> None:
    primo = await _accedi(client)
    await client.post("/api/auth/logout")
    secondo = await _accedi(client)
    assert primo != secondo
    assert (await client.post("/api/prova", headers={"X-CSRF-Token": primo})).status_code == 403
