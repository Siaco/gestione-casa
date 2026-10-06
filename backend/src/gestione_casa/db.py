# SPDX-License-Identifier: AGPL-3.0-or-later
"""Motore e sessioni del database (SQLAlchemy 2, asincrono, driver psycopg 3)."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gestione_casa.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().url_database(), pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dipendenza FastAPI: una sessione per richiesta."""
    async with get_sessionmaker()() as session:
        yield session
