# SPDX-License-Identifier: AGPL-3.0-or-later
"""Comandi di amministrazione da eseguire sul server.

Esempio: ``docker compose exec backend gestione-casa mail-prova --a indirizzo@example.com``
"""

import argparse
import asyncio
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from babel.dates import format_datetime

from gestione_casa.config import get_settings
from gestione_casa.mail import render_mail
from gestione_casa.mail.smtp import MittenteSmtp


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gestione-casa")
    comandi = parser.add_subparsers(dest="comando", required=True)
    prova = comandi.add_parser("mail-prova", help="Invia una mail di prova (attività M0-10)")
    prova.add_argument("--a", dest="destinatario", required=True, help="Indirizzo del destinatario")
    prova.add_argument("--lingua", default=get_settings().lingua_predefinita)
    args = parser.parse_args(argv)

    if args.comando == "mail-prova":
        asyncio.run(_mail_prova(args.destinatario, args.lingua))
        print(f"Mail di prova inviata a {args.destinatario}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
