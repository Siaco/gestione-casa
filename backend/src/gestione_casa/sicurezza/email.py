# SPDX-License-Identifier: AGPL-3.0-or-later
"""Normalizzazione e controllo di base degli indirizzi email."""

import re

from gestione_casa.errors import AppError

# Controllo volutamente semplice: la verifica vera è che la mail arrivi (inviti, recupero)
_FORMATO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LUNGHEZZA_MASSIMA = 254


def normalizza_email(email: str) -> str:
    return email.strip().lower()


def valida_email(email: str) -> str:
    """Restituisce l'email normalizzata o solleva ``auth.email_invalid`` (422)."""
    normalizzata = normalizza_email(email)
    if len(normalizzata) > LUNGHEZZA_MASSIMA or not _FORMATO.match(normalizzata):
        raise AppError("auth.email_invalid", status_code=422)
    return normalizzata
