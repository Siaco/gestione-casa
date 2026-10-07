# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configurazione da variabili d'ambiente (prefisso GC_) e Docker secrets (/run/secrets).

Anche i file dei segreti usano il prefisso: il campo ``db_password`` si legge da
``/run/secrets/gc_db_password`` (in Compose: ``target: gc_db_password``).
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRETS_DIR = Path("/run/secrets")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GC_",
        env_file=".env",
        extra="ignore",
        secrets_dir=SECRETS_DIR if SECRETS_DIR.is_dir() else None,
    )

    ambiente: Literal["sviluppo", "test", "produzione"] = "sviluppo"

    # Database: se database_url è impostato prevale sui singoli parametri
    database_url: SecretStr | None = None
    db_host: str = "localhost"
    db_porta: int = 5432
    db_nome: str = "gestione_casa"
    db_utente: str = "gestione_casa"
    db_password: SecretStr = SecretStr("")

    # Mail
    smtp_host: str = "smtp.gmail.com"
    smtp_porta: int = 587
    smtp_utente: str = ""
    smtp_password: SecretStr = SecretStr("")
    mail_mittente: str = ""
    mail_timeout_secondi: float = 20.0

    # Sicurezza (usata dal WP1)
    session_secret: SecretStr = SecretStr("")

    # Allegati (paragrafo 8.3 del documento iniziale)
    cartella_allegati: Path = Path("/data/allegati")
    allegati_dimensione_massima_mb: int = Field(default=20, ge=1)

    lingua_predefinita: str = "it"
    fuso_orario: str = "Europe/Rome"

    def url_database(self) -> str:
        if self.database_url is not None:
            return self.database_url.get_secret_value()
        password = quote(self.db_password.get_secret_value(), safe="")
        return (
            f"postgresql+psycopg://{quote(self.db_utente, safe='')}:{password}"
            f"@{self.db_host}:{self.db_porta}/{self.db_nome}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
