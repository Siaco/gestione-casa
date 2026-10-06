# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from httpx import AsyncClient

from gestione_casa import __version__

pytestmark = pytest.mark.anyio


@pytest.mark.usefixtures("database")
async def test_health_con_database(client: AsyncClient) -> None:
    risposta = await client.get("/api/health")
    assert risposta.status_code == 200
    assert risposta.json() == {"status": "ok", "database": "ok", "version": __version__}


async def test_health_senza_database(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GC_DATABASE_URL", "postgresql+psycopg://nessuno:nessuna@127.0.0.1:1/inesistente"
    )
    risposta = await client.get("/api/health")
    assert risposta.status_code == 503
    assert risposta.json()["database"] == "error"
