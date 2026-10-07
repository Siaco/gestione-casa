# SPDX-License-Identifier: AGPL-3.0-or-later
"""Applicazione FastAPI."""

from fastapi import FastAPI

from gestione_casa import __version__
from gestione_casa.api import auth, health
from gestione_casa.errors import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gestione casa",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    register_error_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    return app


app = create_app()
