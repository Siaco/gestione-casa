# SPDX-License-Identifier: AGPL-3.0-or-later
"""Errori applicativi con codici stabili.

Il backend non restituisce mai testi per l'utente: restituisce un codice (per esempio
``payment.shares_mismatch``) che il frontend traduce (paragrafo 11.15 del documento iniziale).
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Errore di dominio: codice stabile, stato HTTP, parametri per la traduzione."""

    def __init__(self, code: str, status_code: int = 400, **params: Any) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code
        self.params = params


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "params": exc.params}},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {"field": ".".join(str(p) for p in err["loc"][1:]), "code": f"validation.{err['type']}"}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation.invalid_request", "params": {"fields": fields}}},
        )
