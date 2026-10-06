# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from gestione_casa.config import Settings


def test_url_database_da_parametri(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GC_DATABASE_URL", raising=False)
    s = Settings(db_host="db", db_utente="utente", db_password="p@ss/word", db_nome="casa")
    assert s.url_database() == "postgresql+psycopg://utente:p%40ss%2Fword@db:5432/casa"


def test_segreti_non_esposti_nella_rappresentazione() -> None:
    s = Settings(smtp_password="segreto")
    assert "segreto" not in repr(s)
