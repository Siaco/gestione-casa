# SPDX-License-Identifier: AGPL-3.0-or-later
"""Invio via SMTP con STARTTLS (Gmail con password per le app, o qualsiasi altro SMTP)."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from gestione_casa.config import Settings
from gestione_casa.mail.base import Messaggio


class MittenteSmtp:
    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def _componi(self, messaggio: Messaggio) -> EmailMessage:
        email = EmailMessage()
        email["From"] = self._s.mail_mittente or self._s.smtp_utente
        email["To"] = messaggio.destinatario
        email["Subject"] = messaggio.oggetto
        email.set_content(messaggio.testo)
        if messaggio.html is not None:
            email.add_alternative(messaggio.html, subtype="html")
        return email

    def _invia_sincrono(self, email: EmailMessage) -> None:
        contesto = ssl.create_default_context()
        with smtplib.SMTP(
            self._s.smtp_host, self._s.smtp_porta, timeout=self._s.mail_timeout_secondi
        ) as smtp:
            smtp.starttls(context=contesto)
            smtp.login(self._s.smtp_utente, self._s.smtp_password.get_secret_value())
            smtp.send_message(email)

    async def invia(self, messaggio: Messaggio) -> None:
        await asyncio.to_thread(self._invia_sincrono, self._componi(messaggio))
