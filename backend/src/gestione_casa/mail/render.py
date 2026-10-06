# SPDX-License-Identifier: AGPL-3.0-or-later
"""Composizione delle mail da modelli Jinja2 tradotti nella lingua del destinatario.

Ogni mail ``<modello>`` ha tre file: ``<modello>.subject.txt``, ``<modello>.txt``
e ``<modello>.html``.
I testi sono marcati con ``{% trans %}`` / ``_()`` ed estratti con Babel.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from gestione_casa.i18n import get_translations
from gestione_casa.mail.base import Messaggio

TEMPLATE_DIR = Path(__file__).parent / "templates"


@lru_cache
def _environment(lingua: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(enabled_extensions=("html",), default_for_string=False),
        undefined=StrictUndefined,
        extensions=["jinja2.ext.i18n"],
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.install_gettext_translations(get_translations(lingua), newstyle=True)  # type: ignore[attr-defined]
    return env


def render_mail(modello: str, destinatario: str, lingua: str, **contesto: Any) -> Messaggio:
    env = _environment(lingua)
    contesto = {"lingua": lingua, **contesto}
    oggetto = env.get_template(f"{modello}.subject.txt").render(**contesto).strip()
    testo = env.get_template(f"{modello}.txt").render(**contesto)
    html = env.get_template(f"{modello}.html").render(**contesto)
    return Messaggio(destinatario=destinatario, oggetto=oggetto, testo=testo, html=html)
