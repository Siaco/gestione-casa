# SPDX-License-Identifier: AGPL-3.0-or-later
"""Applicazione FastAPI."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from gestione_casa import __version__
from gestione_casa.api import auth, health, setup
from gestione_casa.auth.primo_avvio import assicura_codice
from gestione_casa.db import get_sessionmaker
from gestione_casa.errors import register_error_handlers
from gestione_casa.sicurezza.csrf import METODI_SICURI, origine_ammessa

logger = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_di_vita(_: FastAPI) -> AsyncIterator[None]:
    """All'avvio, se non ci sono utenti, scrive nei log il codice del primo avvio (M1-06)."""
    try:
        async with get_sessionmaker()() as db:
            if not await setup.esistono_utenti(db):
                assicura_codice()
    except SQLAlchemyError:
        logger.exception("Database non raggiungibile all'avvio: codice del primo avvio rinviato")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=ciclo_di_vita,
        title="Gestione casa",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    register_error_handlers(app)

    @app.middleware("http")
    async def controllo_origine(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Prima difesa CSRF: le modifiche devono arrivare dallo stesso host (M1-04)."""
        if request.method not in METODI_SICURI and not origine_ammessa(
            request.headers.get("origin"),
            request.headers.get("referer"),
            request.headers.get("host"),
        ):
            return JSONResponse(
                status_code=403, content={"error": {"code": "auth.csrf_invalid", "params": {}}}
            )
        return await call_next(request)

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(setup.router, prefix="/api")
    return app


app = create_app()
