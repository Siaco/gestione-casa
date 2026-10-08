# SPDX-License-Identifier: AGPL-3.0-or-later
"""Codice monouso per il primo avvio guidato (paragrafo 9.1, M1-06).

Finché non esistono utenti, il backend genera un codice e lo scrive nei log del server: solo
chi ha accesso al server può creare il primo utente, anche se la pagina di configurazione è
raggiungibile da tutta la rete di casa. Il codice vive in memoria (un solo processo uvicorn)
e cambia a ogni riavvio; dopo la creazione del primo utente non serve più.
"""

import hmac
import logging
import secrets

logger = logging.getLogger("gestione_casa.primo_avvio")

# Senza caratteri ambigui (0/O, 1/I/L): il codice si copia a mano dai log
ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
GRUPPI, LUNGHEZZA_GRUPPO = 3, 4

_codice: str | None = None


def _normalizza(codice: str) -> str:
    return "".join(c for c in codice.upper() if c in ALFABETO)


def assicura_codice() -> str:
    """Genera il codice (una volta per processo) e lo scrive nei log."""
    global _codice
    if _codice is None:
        caratteri = "".join(secrets.choice(ALFABETO) for _ in range(GRUPPI * LUNGHEZZA_GRUPPO))
        _codice = caratteri
        leggibile = "-".join(
            caratteri[i : i + LUNGHEZZA_GRUPPO] for i in range(0, len(caratteri), LUNGHEZZA_GRUPPO)
        )
        logger.warning(
            "Configurazione iniziale richiesta: apri l'app e inserisci il codice %s", leggibile
        )
    return _codice


def codice_corretto(ricevuto: str) -> bool:
    return _codice is not None and hmac.compare_digest(_normalizza(ricevuto), _codice)


def consuma_codice() -> None:
    global _codice
    _codice = None
