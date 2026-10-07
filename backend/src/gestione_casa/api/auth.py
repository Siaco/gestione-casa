# SPDX-License-Identifier: AGPL-3.0-or-later
"""Login, logout e utente corrente (M1-03)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from gestione_casa.auth.dipendenze import Db, UtenteCorrente
from gestione_casa.auth.sessioni import crea_sessione, elimina_sessione, elimina_sessioni_scadute
from gestione_casa.config import Settings, get_settings
from gestione_casa.errors import AppError
from gestione_casa.models import Utente
from gestione_casa.sicurezza.password import LUNGHEZZA_MASSIMA, verifica_fittizia, verifica_password

router = APIRouter(prefix="/auth", tags=["autenticazione"])
Config = Annotated[Settings, Depends(get_settings)]


class Credenziali(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=LUNGHEZZA_MASSIMA)


class UtenteOut(BaseModel):
    id: int
    nome: str
    email: str
    lingua: str

    @classmethod
    def da(cls, utente: Utente) -> "UtenteOut":
        return cls(id=utente.id, nome=utente.nome, email=utente.email, lingua=utente.lingua)


def normalizza_email(email: str) -> str:
    return email.strip().lower()


def _imposta_cookie(risposta: Response, token: str, config: Settings) -> None:
    risposta.set_cookie(
        config.sessione_nome_cookie,
        token,
        max_age=config.sessione_durata_giorni * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=config.cookie_sicuro,
        path="/",
    )


@router.post("/login")
async def login(
    credenziali: Credenziali, request: Request, response: Response, db: Db, config: Config
) -> UtenteOut:
    utente = await db.scalar(
        select(Utente).where(func.lower(Utente.email) == normalizza_email(credenziali.email))
    )
    if utente is None:
        verifica_fittizia(credenziali.password)  # stessi tempi: non si capisce se l'email esiste
        raise AppError("auth.invalid_credentials", status_code=401)
    esito = verifica_password(utente.hash_password, credenziali.password)
    if not esito.valida or not utente.attivo:
        raise AppError("auth.invalid_credentials", status_code=401)
    if esito.nuovo_hash is not None:
        utente.hash_password = esito.nuovo_hash
    await elimina_sessioni_scadute(db)
    token = await crea_sessione(db, utente, request.headers.get("user-agent"))
    await db.commit()
    _imposta_cookie(response, token, config)
    return UtenteOut.da(utente)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: Db, config: Config) -> None:
    token = request.cookies.get(config.sessione_nome_cookie)
    if token:
        await elimina_sessione(db, token)
        await db.commit()
    response.delete_cookie(
        config.sessione_nome_cookie,
        path="/",
        httponly=True,
        samesite="lax",
        secure=config.cookie_sicuro,
    )


@router.get("/me")
async def me(utente: UtenteCorrente) -> UtenteOut:
    return UtenteOut.da(utente)
