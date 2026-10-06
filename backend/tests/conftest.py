# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixture comuni. I test d'integrazione usano un PostgreSQL reale indicato da GC_DATABASE_URL.

In locale: ``docker compose -f infra/compose.yaml -f infra/compose.dev.yaml up -d db`` e
``GC_DATABASE_URL=postgresql+psycopg://gestione_casa:<password>@localhost:5432/gestione_casa_test``.
"""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from gestione_casa.config import get_settings
from gestione_casa.db import get_engine, get_sessionmaker
from gestione_casa.main import create_app

BACKEND = Path(__file__).resolve().parent.parent

os.environ.setdefault("GC_AMBIENTE", "test")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


def _svuota_cache() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()


@pytest.fixture(autouse=True)
def cache_pulite() -> Iterator[None]:
    """Ogni test legge la configurazione corrente (le variabili d'ambiente possono cambiare)."""
    _svuota_cache()
    yield
    _svuota_cache()


def _richiede_database() -> None:
    if not os.environ.get("GC_DATABASE_URL"):
        pytest.skip("GC_DATABASE_URL non impostata: test d'integrazione saltato")


@pytest.fixture
def alembic_config() -> Config:
    _richiede_database()
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    return cfg


@pytest.fixture
def database(alembic_config: Config) -> Iterator[None]:
    """Schema aggiornato all'ultima migrazione, rimosso a fine test."""
    command.upgrade(alembic_config, "head")
    yield
    command.downgrade(alembic_config, "base")


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await get_engine().dispose()
