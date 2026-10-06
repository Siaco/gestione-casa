# SPDX-License-Identifier: AGPL-3.0-or-later
"""Traduzioni dei testi generati dal backend (mail), con Babel/gettext.

I cataloghi stanno in ``i18n/locale/<lingua>/LC_MESSAGES/messages.po`` e vengono compilati
in ``.mo`` (``pybabel compile``) durante la build; in sviluppo, se il ``.mo`` manca, si usa
direttamente il ``.po``.
"""

import io
from functools import lru_cache
from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from babel.support import NullTranslations, Translations

LOCALE_DIR = Path(__file__).parent / "locale"
DOMAIN = "messages"
LINGUA_RIFERIMENTO = "it"


def lingue_disponibili() -> list[str]:
    return sorted(p.name for p in LOCALE_DIR.iterdir() if (p / "LC_MESSAGES").is_dir())


@lru_cache
def get_translations(lingua: str) -> NullTranslations:
    """Traduzioni per la lingua richiesta, con ripiego sulla lingua di riferimento."""
    if lingua not in lingue_disponibili():
        lingua = LINGUA_RIFERIMENTO
    cartella = LOCALE_DIR / lingua / "LC_MESSAGES"
    mo = cartella / f"{DOMAIN}.mo"
    if not mo.exists():
        po = cartella / f"{DOMAIN}.po"
        if not po.exists():
            return NullTranslations()
        with po.open("rb") as f:
            catalogo = read_po(f, locale=lingua)
        buffer = io.BytesIO()
        write_mo(buffer, catalogo)
        buffer.seek(0)
        return Translations(fp=buffer, domain=DOMAIN)
    return Translations.load(str(LOCALE_DIR), [lingua], DOMAIN)
