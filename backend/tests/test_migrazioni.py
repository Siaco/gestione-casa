# SPDX-License-Identifier: AGPL-3.0-or-later
"""Le migrazioni salgono e scendono senza errori e il modello coincide con lo schema."""

import asyncio

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy.ext.asyncio import create_async_engine

from gestione_casa.config import get_settings
from gestione_casa.models import Base

# Tabelle definite solo nei test (prefisso "prova_"): non fanno parte dello schema
PREFISSO_TABELLE_DI_PROVA = "prova_"


def _includi(oggetto: object, nome: str | None, tipo: str, *_: object) -> bool:
    return not (tipo == "table" and (nome or "").startswith(PREFISSO_TABELLE_DI_PROVA))


def _differenze() -> list[object]:
    async def _esegui() -> list[object]:
        engine = create_async_engine(get_settings().url_database())
        async with engine.connect() as conn:
            diff = await conn.run_sync(
                lambda sync: compare_metadata(
                    MigrationContext.configure(sync, opts={"include_object": _includi}),
                    Base.metadata,
                )
            )
        await engine.dispose()
        return list(diff)

    return asyncio.run(_esegui())


def test_upgrade_downgrade_upgrade(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    try:
        assert _differenze() == [], (
            "Il modello non coincide con le migrazioni: serve una nuova migrazione"
        )
    finally:
        command.downgrade(alembic_config, "base")
