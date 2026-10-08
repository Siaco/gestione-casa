# SPDX-License-Identifier: AGPL-3.0-or-later
"""Limitazione dei tentativi di accesso (M1-05)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from gestione_casa.config import get_settings
from gestione_casa.models import TentativoFallito, Utente
from gestione_casa.sicurezza.limiti import MASSIMO
from gestione_casa.sicurezza.password import calcola_hash

pytestmark = pytest.mark.anyio
PASSWORD = "una password lunga"


@pytest.fixture
def engine(database: None) -> Iterator[Engine]:
    e = create_engine(get_settings().url_database())
    with Session(e) as s:
        s.add(Utente(nome="Camillo", email="c@example.com", hash_password=calcola_hash(PASSWORD)))
        s.commit()
    yield e
    e.dispose()


async def _login(client: AsyncClient, password: str, email: str = "c@example.com") -> int:
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    return r.status_code


async def test_sesto_tentativo_bloccato_anche_con_password_giusta(
    client: AsyncClient, engine: Engine
) -> None:
    for _ in range(MASSIMO):
        assert await _login(client, "password sbagliata") == 401
    r = await client.post("/api/auth/login", json={"email": "c@example.com", "password": PASSWORD})
    assert r.status_code == 429
    errore = r.json()["error"]
    assert errore["code"] == "auth.too_many_attempts"
    assert 0 < errore["params"]["retry_after"] <= 15 * 60
    assert errore["params"]["minutes"] == 15
    assert r.headers["Retry-After"] == str(errore["params"]["retry_after"])


async def test_blocco_per_ip_anche_cambiando_email(client: AsyncClient, engine: Engine) -> None:
    for i in range(MASSIMO):
        await _login(client, "x", email=f"tentativo{i}@example.com")
    assert await _login(client, PASSWORD) == 429


async def test_blocco_scade_dopo_la_finestra(client: AsyncClient, engine: Engine) -> None:
    for _ in range(MASSIMO):
        await _login(client, "password sbagliata")
    with Session(engine) as s:
        s.execute(
            update(TentativoFallito).values(avvenuto_il=datetime.now(UTC) - timedelta(minutes=16))
        )
        s.commit()
    assert await _login(client, PASSWORD) == 200


async def test_accesso_riuscito_azzera_solo_l_email(client: AsyncClient, engine: Engine) -> None:
    for _ in range(MASSIMO - 1):
        await _login(client, "password sbagliata")
    assert await _login(client, PASSWORD) == 200
    with Session(engine) as s:
        chiavi = set(s.scalars(select(TentativoFallito.chiave)))
    assert chiavi == {"ip:127.0.0.1"}


async def test_tentativi_bloccati_non_registrati(client: AsyncClient, engine: Engine) -> None:
    for _ in range(MASSIMO + 3):
        await _login(client, "password sbagliata")
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(TentativoFallito)) == MASSIMO * 2


async def test_tentativi_vecchi_eliminati(client: AsyncClient, engine: Engine) -> None:
    await _login(client, "password sbagliata")
    with Session(engine) as s:
        s.execute(
            update(TentativoFallito).values(avvenuto_il=datetime.now(UTC) - timedelta(days=2))
        )
        s.commit()
    await _login(client, "password sbagliata")
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(TentativoFallito)) == 2
