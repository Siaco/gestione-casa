# SPDX-License-Identifier: AGPL-3.0-or-later
"""Primo avvio guidato: creazione del primo utente con il codice dei log (M1-06)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text

from gestione_casa.api.auth import SessioneOut, UtenteOut, imposta_cookie_sessione
from gestione_casa.auth.dipendenze import Db
from gestione_casa.auth.primo_avvio import assicura_codice, codice_corretto, consuma_codice
from gestione_casa.auth.sessioni import crea_sessione
from gestione_casa.config import Settings, get_settings
from gestione_casa.errors import AppError
from gestione_casa.models import Utente
from gestione_casa.sicurezza.csrf import token_csrf
from gestione_casa.sicurezza.email import valida_email
from gestione_casa.sicurezza.limiti import Ambito, chiavi, registra_fallimento, verifica_limite
from gestione_casa.sicurezza.password import calcola_hash, valida_password

router = APIRouter(prefix="/setup", tags=["primo avvio"])
Config = Annotated[Settings, Depends(get_settings)]

# Serializza le richieste concorrenti: un solo "primo utente"
CHIAVE_LOCK_PRIMO_AVVIO = 7_100_001


class StatoPrimoAvvio(BaseModel):
    necessaria: bool


class DatiPrimoUtente(BaseModel):
    codice: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1000)
    lingua: str = Field(default="it", pattern=r"^[a-z]{2}$")


async def esistono_utenti(db: Db) -> bool:
    return bool(await db.scalar(select(func.count()).select_from(Utente)))


@router.get("")
async def stato(db: Db) -> StatoPrimoAvvio:
    necessaria = not await esistono_utenti(db)
    if necessaria:
        assicura_codice()
    return StatoPrimoAvvio(necessaria=necessaria)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crea_primo_utente(
    dati: DatiPrimoUtente, request: Request, response: Response, db: Db, config: Config
) -> SessioneOut:
    limitate = chiavi(request)
    await verifica_limite(db, Ambito.PRIMO_AVVIO, limitate)
    await db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": CHIAVE_LOCK_PRIMO_AVVIO})
    if await esistono_utenti(db):
        raise AppError("setup.already_done", status_code=409)
    if not codice_corretto(dati.codice):
        await registra_fallimento(db, Ambito.PRIMO_AVVIO, limitate)
        await db.commit()
        raise AppError("setup.invalid_code", status_code=403)
    email = valida_email(dati.email)
    valida_password(dati.password, email)

    utente = Utente(
        nome=dati.nome.strip(),
        email=email,
        hash_password=calcola_hash(dati.password),
        lingua=dati.lingua,
    )
    db.add(utente)
    await db.flush()
    token = await crea_sessione(db, utente, request.headers.get("user-agent"))
    await db.commit()
    consuma_codice()
    imposta_cookie_sessione(response, token, config)
    return SessioneOut(utente=UtenteOut.da(utente), csrf_token=token_csrf(token))
