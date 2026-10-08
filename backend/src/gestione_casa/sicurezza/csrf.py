# SPDX-License-Identifier: AGPL-3.0-or-later
"""Protezione CSRF (M1-04).

Due difese complementari:

1. **Origine**: ogni richiesta che modifica dati e porta un'intestazione ``Origin`` (o, in sua
   assenza, ``Referer``) deve provenire dallo stesso host dell'app. I browser la inviano
   sempre per le richieste tra siti diversi; client senza ``Origin`` (curl, test) non sono
   un veicolo di CSRF.
2. **Token legato alla sessione**: gli endpoint autenticati che modificano dati richiedono
   l'intestazione ``X-CSRF-Token``, uguale all'HMAC del token di sessione. Il frontend lo
   riceve dal login e da ``/api/auth/me`` e lo tiene in memoria; un sito esterno non può
   leggerlo né calcolarlo.

Il token non si salva: si ricalcola dal cookie di sessione e cambia a ogni nuova sessione.
"""

import hashlib
import hmac
import logging
import secrets
from functools import lru_cache
from urllib.parse import urlsplit

from gestione_casa.config import get_settings

INTESTAZIONE = "X-CSRF-Token"
METODI_SICURI = frozenset({"GET", "HEAD", "OPTIONS"})

logger = logging.getLogger(__name__)


@lru_cache
def _chiave() -> bytes:
    chiave = get_settings().session_secret.get_secret_value()
    if not chiave:
        # Solo sviluppo e test: in produzione il segreto arriva da Docker secrets
        logger.warning("session_secret non impostato: chiave CSRF casuale valida fino al riavvio")
        return secrets.token_bytes(32)
    return chiave.encode()


def token_csrf(token_sessione: str) -> str:
    return hmac.new(_chiave(), b"csrf:" + token_sessione.encode(), hashlib.sha256).hexdigest()


def token_valido(token_sessione: str, ricevuto: str | None) -> bool:
    return ricevuto is not None and hmac.compare_digest(token_csrf(token_sessione), ricevuto)


def origine_ammessa(origin: str | None, referer: str | None, host: str | None) -> bool:
    """``True`` se l'origine dichiarata è assente o coincide con l'host della richiesta."""
    dichiarata = origin or referer
    if dichiarata is None:
        return True
    if dichiarata == "null" or host is None:
        return False
    return urlsplit(dichiarata).netloc.lower() == host.lower()
