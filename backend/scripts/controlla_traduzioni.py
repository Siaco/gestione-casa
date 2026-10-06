# SPDX-License-Identifier: AGPL-3.0-or-later
"""Controllo dei testi traducibili del backend, eseguito nella pipeline.

1. Il modello ``messages.pot`` è aggiornato rispetto al codice e ai modelli mail.
2. Ogni lingua diversa da quella di riferimento (``it``) traduce tutti i testi.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from babel.messages.pofile import read_po

RADICE = Path(__file__).resolve().parent.parent
LOCALE = RADICE / "src" / "gestione_casa" / "i18n" / "locale"
RIFERIMENTO = "it"


def _msgids(percorso: Path) -> set[str]:
    with percorso.open("rb") as f:
        return {str(m.id) for m in read_po(f) if m.id}


def main() -> int:
    errori: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        nuovo = Path(tmp) / "messages.pot"
        subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "babel.messages.frontend",
                "-q",
                "extract",
                "-F",
                "babel.cfg",
                "-o",
                str(nuovo),
                "--no-location",
                ".",
            ],
            cwd=RADICE,
            check=True,
        )
        attesi = _msgids(nuovo)
    presenti = _msgids(LOCALE / "messages.pot")
    if attesi != presenti:
        errori.append(
            "messages.pot non aggiornato: esegui 'uv run pybabel extract' e 'pybabel update' "
            f"(mancanti: {sorted(attesi - presenti)}, superflui: {sorted(presenti - attesi)})"
        )

    for po in sorted(LOCALE.glob("*/LC_MESSAGES/messages.po")):
        lingua = po.parent.parent.name
        with po.open("rb") as f:
            catalogo = read_po(f)
        ids = {str(m.id) for m in catalogo if m.id}
        if ids != attesi:
            errori.append(
                f"{lingua}: catalogo non allineato al modello (eseguire 'pybabel update')"
            )
        if lingua != RIFERIMENTO:
            vuoti = [str(m.id) for m in catalogo if m.id and not m.string]
            if vuoti:
                errori.append(f"{lingua}: {len(vuoti)} testi senza traduzione")

    for e in errori:
        print(f"ERRORE: {e}", file=sys.stderr)
    if not errori:
        print("Traduzioni del backend: OK")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
