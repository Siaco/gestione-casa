# SPDX-License-Identifier: AGPL-3.0-or-later
"""Token casuali per inviti, recupero password e sessioni.

Il token in chiaro va solo all'utente (link o cookie); nel database si salva l'impronta.
SHA-256 basta: i token sono casuali a 256 bit, non password da proteggere con un hash lento.
"""

import hashlib
import hmac
import secrets
from typing import NamedTuple

BYTE_CASUALI = 32


class TokenGenerato(NamedTuple):
    token: str
    """Valore da consegnare all'utente, mai salvato."""
    impronta: str
    """Valore da salvare nel database."""


def impronta(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def genera_token() -> TokenGenerato:
    token = secrets.token_urlsafe(BYTE_CASUALI)
    return TokenGenerato(token=token, impronta=impronta(token))


def corrisponde(token: str, impronta_salvata: str) -> bool:
    """Confronto a tempo costante tra un token ricevuto e un'impronta salvata."""
    return hmac.compare_digest(impronta(token), impronta_salvata)
