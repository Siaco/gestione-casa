# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from gestione_casa.mail import render_mail
from gestione_casa.mail.base import MittenteInMemoria

pytestmark = pytest.mark.anyio


async def test_mail_di_prova_in_italiano() -> None:
    messaggio = render_mail(
        "prova", destinatario="a@example.com", lingua="it", nome="Aurora", data="oggi"
    )
    assert messaggio.oggetto == "Gestione casa: mail di prova"
    assert "Ciao Aurora," in messaggio.testo
    assert messaggio.html is not None and 'lang="it"' in messaggio.html

    mittente = MittenteInMemoria()
    await mittente.invia(messaggio)
    assert mittente.inviati == [messaggio]


def test_lingua_sconosciuta_ripiega_sull_italiano() -> None:
    messaggio = render_mail("prova", destinatario="a@example.com", lingua="xx", nome="A", data="d")
    assert messaggio.oggetto == "Gestione casa: mail di prova"


def test_html_con_escape() -> None:
    messaggio = render_mail(
        "prova", destinatario="a@example.com", lingua="it", nome="<b>x</b>", data="d"
    )
    assert messaggio.html is not None and "<b>x</b>" not in messaggio.html
