# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from gestione_casa.errors import AppError, register_error_handlers

pytestmark = pytest.mark.anyio


async def test_errore_restituisce_codice_stabile() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/errore")
    async def _errore() -> None:
        raise AppError("payment.shares_mismatch", status_code=409, differenza=1)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/errore")
    assert r.status_code == 409
    assert r.json() == {"error": {"code": "payment.shares_mismatch", "params": {"differenza": 1}}}
