# SPDX-License-Identifier: AGPL-3.0-or-later
"""Login, logout, utente corrente e ciclo di vita delle sessioni (M1-03)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from argon2 import PasswordHasher
from httpx import AsyncClient, Response
from sqlalchemy import create_engine, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from gestione_casa.config import get_settings
from gestione_casa.models import Sessione, Utente
from gestione_casa.sicurezza.password import calcola_hash
from gestione_casa.sicurezza.token import impronta

pytestmark = pytest.mark.anyio

PASSWORD = "una password lunga"
COOKIE = "gc_sessione"


@pytest.fixture
def engine(database: None) -> Iterator[Engine]:
    e = create_engine(get_settings().url_database())
    with Session(e) as s:
        s.add(
            Utente(
                nome="Camillo", email="Camillo@Example.com", hash_password=calcola_hash(PASSWORD)
            )
        )
        s.commit()
    yield e
    e.dispose()


async def _login(
    client: AsyncClient, email: str = "camillo@example.com", password: str = PASSWORD
) -> Response:
    return await client.post("/api/auth/login", json={"email": email, "password": password})


def _sessioni(engine: Engine) -> list[Sessione]:
    with Session(engine) as s:
        return list(s.scalars(select(Sessione)))


async def test_login_riuscito_imposta_un_cookie_sicuro(client: AsyncClient, engine: Engine) -> None:
    r = await _login(client, email="  CAMILLO@example.com ")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["utente"] == {
        "id": 1,
        "nome": "Camillo",
        "email": "Camillo@Example.com",
        "lingua": "it",
    }
    assert len(corpo["csrf_token"]) == 64
    intestazione = r.headers["set-cookie"].lower()
    assert intestazione.startswith(f"{COOKIE}=")
    assert (
        "httponly" in intestazione and "samesite=lax" in intestazione and "path=/" in intestazione
    )
    assert "secure" not in intestazione  # 1.0: HTTP in rete locale

    token = r.cookies[COOKIE]
    [sessione] = _sessioni(engine)
    assert sessione.impronta_token == impronta(token) and token != sessione.impronta_token

    me = await client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["utente"]["nome"] == "Camillo"
    assert me.json()["csrf_token"] == corpo["csrf_token"]


@pytest.mark.parametrize(
    ("email", "password"),
    [("camillo@example.com", "password sbagliata"), ("nessuno@example.com", PASSWORD)],
)
async def test_credenziali_errate_stessa_risposta(
    client: AsyncClient, engine: Engine, email: str, password: str
) -> None:
    r = await _login(client, email, password)
    assert r.status_code == 401
    assert r.json() == {"error": {"code": "auth.invalid_credentials", "params": {}}}
    assert COOKIE not in r.cookies
    assert _sessioni(engine) == []


async def test_utente_disattivato_non_accede(client: AsyncClient, engine: Engine) -> None:
    with Session(engine) as s:
        s.execute(update(Utente).values(attivo=False))
        s.commit()
    assert (await _login(client)).status_code == 401


async def test_utente_disattivato_perde_la_sessione(client: AsyncClient, engine: Engine) -> None:
    await _login(client)
    with Session(engine) as s:
        s.execute(update(Utente).values(attivo=False))
        s.commit()
    assert (await client.get("/api/auth/me")).status_code == 401
    assert _sessioni(engine) == []


async def test_senza_sessione_accesso_negato(client: AsyncClient, engine: Engine) -> None:
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.not_authenticated"
    client.cookies.set(COOKIE, "token-inventato")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_logout(client: AsyncClient, engine: Engine) -> None:
    await _login(client)
    r = await client.post("/api/auth/logout")
    assert r.status_code == 204
    assert (
        f'{COOKIE}=""' in r.headers["set-cookie"] or "max-age=0" in r.headers["set-cookie"].lower()
    )
    assert _sessioni(engine) == []
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_logout_senza_sessione(client: AsyncClient, engine: Engine) -> None:
    assert (await client.post("/api/auth/logout")).status_code == 204


async def test_sessione_scaduta(client: AsyncClient, engine: Engine) -> None:
    await _login(client)
    with Session(engine) as s:
        s.execute(update(Sessione).values(scade_il=datetime.now(UTC) - timedelta(seconds=1)))
        s.commit()
    assert (await client.get("/api/auth/me")).status_code == 401
    assert _sessioni(engine) == []


async def test_rinnovo_con_l_uso(client: AsyncClient, engine: Engine) -> None:
    await _login(client)
    due_ore_fa = datetime.now(UTC) - timedelta(hours=2)
    tra_un_giorno = datetime.now(UTC) + timedelta(days=1)
    with Session(engine) as s:
        s.execute(update(Sessione).values(ultimo_uso=due_ore_fa, scade_il=tra_un_giorno))
        s.commit()
    assert (await client.get("/api/auth/me")).status_code == 200
    [sessione] = _sessioni(engine)
    assert sessione.ultimo_uso > due_ore_fa
    assert sessione.scade_il > datetime.now(UTC) + timedelta(days=29)


async def test_nessun_rinnovo_se_usata_da_poco(client: AsyncClient, engine: Engine) -> None:
    await _login(client)
    [prima] = _sessioni(engine)
    await client.get("/api/auth/me")
    [dopo] = _sessioni(engine)
    assert dopo.scade_il == prima.scade_il


async def test_login_elimina_le_sessioni_scadute(client: AsyncClient, engine: Engine) -> None:
    await _login(client)
    with Session(engine) as s:
        s.execute(update(Sessione).values(scade_il=datetime.now(UTC) - timedelta(days=1)))
        s.commit()
    await _login(client)
    assert len(_sessioni(engine)) == 1


async def test_hash_aggiornato_al_login(client: AsyncClient, engine: Engine) -> None:
    vecchio = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    with Session(engine) as s:
        s.execute(update(Utente).values(hash_password=vecchio))
        s.commit()
    assert (await _login(client)).status_code == 200
    with Session(engine) as s:
        assert s.scalar(select(Utente.hash_password)) != vecchio


async def test_dispositivo_registrato(client: AsyncClient, engine: Engine) -> None:
    await client.post(
        "/api/auth/login",
        json={"email": "camillo@example.com", "password": PASSWORD},
        headers={"User-Agent": "Telefono di prova " + "x" * 400},
    )
    [sessione] = _sessioni(engine)
    assert sessione.dispositivo is not None
    assert sessione.dispositivo.startswith("Telefono di prova") and len(sessione.dispositivo) == 255


async def test_richiesta_non_valida(client: AsyncClient, engine: Engine) -> None:
    r = await client.post("/api/auth/login", json={"email": "x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation.invalid_request"
