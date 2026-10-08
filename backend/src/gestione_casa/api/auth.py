# SPDX-License-Identifier: AGPL-3.0-or-later
"""Login, logout e utente corrente (M1-03)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from gestione_casa.auth.dipendenze import Db, sessione_corrente
from gestione_casa.auth.sessioni import (
    SessioneAttiva,
    crea_sessione,
    elimina_sessione,
    elimina_sessioni_scadute,
)
from gestione_casa.config import Settings, get_settings
from gestione_casa.errors import AppError
from gestione_casa.models import Utente
from gestione_casa.sicurezza.csrf import token_csrf
from gestione_casa.sicurezza.limiti import (
    Ambito,
    azzera,
    chiavi,
    registra_fallimento,
    verifica_limite,
)
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


class SessioneOut(BaseModel):
    """Utente e token CSRF da inviare nell'intestazione X-CSRF-Token (M1-04)."""

    utente: UtenteOut
    csrf_token: str


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
) -> SessioneOut:
    email = normalizza_email(credenziali.email)
    limitate = chiavi(request, email)
    await verifica_limite(db, Ambito.LOGIN, limitate)
    utente = await db.scalar(select(Utente).where(func.lower(Utente.email) == email))
    if utente is None:
        verifica_fittizia(credenziali.password)  # stessi tempi: non si capisce se l'email esiste
        esito = None
    else:
        esito = verifica_password(utente.hash_password, credenziali.password)
    if utente is None or esito is None or not esito.valida or not utente.attivo:
        await registra_fallimento(db, Ambito.LOGIN, limitate)
        await db.commit()
        raise AppError("auth.invalid_credentials", status_code=401)
    if esito.nuovo_hash is not None:
        utente.hash_password = esito.nuovo_hash
    # Si azzera solo l'email: un accesso riuscito non deve sbloccare un indirizzo IP sospetto
    await azzera(db, Ambito.LOGIN, [c for c in limitate if c.startswith("email:")])
    await elimina_sessioni_scadute(db)
    token = await crea_sessione(db, utente, request.headers.get("user-agent"))
    await db.commit()
    _imposta_cookie(response, token, config)
    return SessioneOut(utente=UtenteOut.da(utente), csrf_token=token_csrf(token))


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
async def me(
    request: Request,
    attiva: Annotated[SessioneAttiva, Depends(sessione_corrente)],
    config: Config,
) -> SessioneOut:
    token = request.cookies[config.sessione_nome_cookie]
    return SessioneOut(utente=UtenteOut.da(attiva.utente), csrf_token=token_csrf(token))
