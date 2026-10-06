# SPDX-License-Identifier: AGPL-3.0-or-later
"""Interfaccia del livello di invio."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Messaggio:
    destinatario: str
    oggetto: str
    testo: str
    html: str | None = None


class MittenteMail(Protocol):
    """Qualsiasi canale di invio (SMTP Gmail, altro SMTP, servizio esterno, finto nei test)."""

    async def invia(self, messaggio: Messaggio) -> None: ...


class MittenteInMemoria:
    """Mittente per test e sviluppo: conserva i messaggi invece di inviarli."""

    def __init__(self) -> None:
        self.inviati: list[Messaggio] = []

    async def invia(self, messaggio: Messaggio) -> None:
        self.inviati.append(messaggio)
