# SPDX-License-Identifier: AGPL-3.0-or-later
"""I segreti montati da Docker Compose arrivano davvero nella configurazione."""

from pathlib import Path

import pytest
import yaml

from gestione_casa.config import Settings

COMPOSE = Path(__file__).resolve().parents[2] / "infra" / "compose.yaml"


def test_segreti_letti_con_prefisso(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GC_DB_PASSWORD", raising=False)
    (tmp_path / "gc_db_password").write_text("segreto-db")
    (tmp_path / "gc_smtp_password").write_text("segreto-smtp")
    s = Settings(_secrets_dir=tmp_path)
    assert s.db_password.get_secret_value() == "segreto-db"
    assert s.smtp_password.get_secret_value() == "segreto-smtp"


def test_compose_monta_i_segreti_con_i_nomi_attesi() -> None:
    compose = yaml.safe_load(COMPOSE.read_text())
    segreti = compose["services"]["backend"]["secrets"]
    campi = set(Settings.model_fields)
    for segreto in segreti:
        target = segreto["target"]
        assert target.startswith("gc_"), f"{target}: manca il prefisso gc_"
        assert target.removeprefix("gc_") in campi, f"{target}: nessun campo corrispondente"
