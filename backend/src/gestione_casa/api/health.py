# SPDX-License-Identifier: AGPL-3.0-or-later
"""Controllo dello stato del servizio, usato dal frontend e dal monitoraggio."""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from gestione_casa import __version__
from gestione_casa.db import get_session

router = APIRouter(tags=["sistema"])
logger = logging.getLogger(__name__)

Stato = Literal["ok", "error"]


class HealthResponse(BaseModel):
    status: Stato
    database: Stato
    version: str


@router.get("/health")
async def health(
    response: Response, session: Annotated[AsyncSession, Depends(get_session)]
) -> HealthResponse:
    database: Stato = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError):
        logger.exception("Database non raggiungibile")
        database = "error"
    if database != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status=database, database=database, version=__version__)
