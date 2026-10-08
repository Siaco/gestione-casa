# SPDX-License-Identifier: AGPL-3.0-or-later
"""Comandi di amministrazione da eseguire sul server.

Esempi:

- ``docker compose exec backend gestione-casa mail-prova --a indirizzo@example.com``
- ``docker compose exec -it backend gestione-casa reimposta-password --email indirizzo@example.com``

I messaggi del terminale sono per l'amministratore di sistema e restano in italiano.
"""

import argparse
import asyncio
import getpass
import sys
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from babel.dates import format_datetime
from sqlalchemy import func, select

from gestione_casa.auth.sessioni import elimina_sessioni_utente
from gestione_casa.config import get_settings
from gestione_casa.db import get_engine, get_sessionmaker
from gestione_casa.errors import AppError
from gestione_casa.mail import render_mail
from gestione_casa.mail.smtp import MittenteSmtp
from gestione_casa.models import Utente
from gestione_casa.sicurezza.password import calcola_hash, valida_password

MESSAGGI_PASSWORD = {
    "auth.password_too_short": "La password deve avere almeno {min} caratteri.",
    "auth.password_too_long": "La password può avere al massimo {max} caratteri.",
    "auth.password_equals_email": "La password non può essere uguale all'email.",
}


async def _mail_prova(destinatario: str, lingua: str) -> None:
    settings = get_settings()
    adesso = datetime.now(ZoneInfo(settings.fuso_orario))
    messaggio = render_mail(
        "prova",
        destinatario=destinatario,
        lingua=lingua,
        nome=destinatario,
        data=format_datetime(adesso, "full", locale=lingua),
    )
    await MittenteSmtp(settings).invia(messaggio)


async def reimposta_password(
    email: str, chiedi: Callable[[str], str] | None = None
) -> tuple[bool, str]:
    """Imposta una nuova password e chiude tutte le sessioni dell'utente (M1-09).

    Restituisce l'esito e il messaggio per l'amministratore.
    """
    leggi = chiedi or getpass.getpass
    try:
        async with get_sessionmaker()() as db:
            utente = await db.scalar(
                select(Utente).where(func.lower(Utente.email) == email.strip().lower())
            )
            if utente is None:
                return False, f"Nessun utente con email {email}."
            password = leggi("Nuova password: ")
            if password != leggi("Ripeti la nuova password: "):
                return False, "Le due password non coincidono: nessuna modifica."
            try:
                valida_password(password, utente.email)
            except AppError as errore:
                messaggio = MESSAGGI_PASSWORD.get(errore.code, errore.code)
                return False, messaggio.format(**errore.params)
            utente.hash_password = calcola_hash(password)
            await elimina_sessioni_utente(db, utente.id)
            await db.commit()
            return True, f"Password di {utente.email} reimpostata; sessioni attive chiuse."
    finally:
        await get_engine().dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gestione-casa")
    comandi = parser.add_subparsers(dest="comando", required=True)
    prova = comandi.add_parser("mail-prova", help="Invia una mail di prova (attività M0-10)")
    prova.add_argument("--a", dest="destinatario", required=True, help="Indirizzo del destinatario")
    prova.add_argument("--lingua", default=get_settings().lingua_predefinita)
    reimposta = comandi.add_parser(
        "reimposta-password",
        help="Reimposta la password di un utente (emergenza, per esempio senza mail)",
    )
    reimposta.add_argument("--email", required=True, help="Email dell'utente")
    args = parser.parse_args(argv)

    if args.comando == "mail-prova":
        asyncio.run(_mail_prova(args.destinatario, args.lingua))
        print(f"Mail di prova inviata a {args.destinatario}")
    elif args.comando == "reimposta-password":
        riuscito, messaggio = asyncio.run(reimposta_password(args.email))
        print(messaggio, file=sys.stdout if riuscito else sys.stderr)
        return 0 if riuscito else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
