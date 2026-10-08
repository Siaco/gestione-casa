# SPDX-License-Identifier: AGPL-3.0-or-later
"""Applicazione FastAPI."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from gestione_casa import __version__
from gestione_casa.api import auth, health
from gestione_casa.errors import register_error_handlers
from gestione_casa.sicurezza.csrf import METODI_SICURI, origine_ammessa


def create_app() -> FastAPI:
    app = FastAPI(
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
    return app


app = create_app()
