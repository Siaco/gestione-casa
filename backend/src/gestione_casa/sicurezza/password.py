# SPDX-License-Identifier: AGPL-3.0-or-later
"""Password: regole, hash argon2id e verifica (M1-02).

Regole volutamente semplici (linee guida NIST SP 800-63B): lunghezza minima, nessun vincolo
di composizione, password diversa dall'email. I parametri di argon2 sono quelli predefiniti
della libreria; se cambiano, ``verifica_password`` restituisce un nuovo hash da salvare.
"""

import unicodedata
from typing import NamedTuple

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from gestione_casa.errors import AppError

LUNGHEZZA_MINIMA = 12
LUNGHEZZA_MASSIMA = 256  # evita di far calcolare hash su testi enormi

_hasher = PasswordHasher()
# Hash calcolato una volta, usato per pareggiare i tempi quando l'utente non esiste
_HASH_FITTIZIO = _hasher.hash("password-fittizia-per-pareggiare-i-tempi")


def _normalizza(password: str) -> str:
    # Stessa password digitata con tastiere diverse (per esempio "é" composta o precomposta)
    return unicodedata.normalize("NFKC", password)


def valida_password(password: str, email: str | None = None) -> None:
    """Solleva ``AppError`` con un codice stabile se la password non rispetta le regole."""
    p = _normalizza(password)
    if len(p) < LUNGHEZZA_MINIMA:
        raise AppError("auth.password_too_short", status_code=422, min=LUNGHEZZA_MINIMA)
    if len(p) > LUNGHEZZA_MASSIMA:
        raise AppError("auth.password_too_long", status_code=422, max=LUNGHEZZA_MASSIMA)
    if email is not None and p.strip().casefold() == email.strip().casefold():
        raise AppError("auth.password_equals_email", status_code=422)


def calcola_hash(password: str) -> str:
    return _hasher.hash(_normalizza(password))


class EsitoVerifica(NamedTuple):
    valida: bool
    nuovo_hash: str | None = None
    """Valorizzato se l'hash salvato usa parametri superati e va sostituito."""


def verifica_password(hash_salvato: str, password: str) -> EsitoVerifica:
    p = _normalizza(password)
    try:
        _hasher.verify(hash_salvato, p)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return EsitoVerifica(valida=False)
    if _hasher.check_needs_rehash(hash_salvato):
        return EsitoVerifica(valida=True, nuovo_hash=_hasher.hash(p))
    return EsitoVerifica(valida=True)


def verifica_fittizia(password: str) -> None:
    """Da chiamare quando l'utente non esiste: stessi tempi di una verifica reale."""
    verifica_password(_HASH_FITTIZIO, password)
