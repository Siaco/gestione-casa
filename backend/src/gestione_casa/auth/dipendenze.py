# SPDX-License-Identifier: AGPL-3.0-or-later
"""Dipendenze FastAPI per gli endpoint protetti."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gestione_casa.auth.sessioni import SessioneAttiva, trova_sessione
from gestione_casa.config import get_settings
from gestione_casa.db import get_session
from gestione_casa.errors import AppError
from gestione_casa.models import Utente

Db = Annotated[AsyncSession, Depends(get_session)]


async def sessione_corrente(request: Request, db: Db) -> SessioneAttiva:
    token = request.cookies.get(get_settings().sessione_nome_cookie)
    attiva = await trova_sessione(db, token) if token else None
    if attiva is None:
        raise AppError("auth.not_authenticated", status_code=401)
    return attiva


async def utente_corrente(
    attiva: Annotated[SessioneAttiva, Depends(sessione_corrente)],
) -> Utente:
    return attiva.utente


UtenteCorrente = Annotated[Utente, Depends(utente_corrente)]
