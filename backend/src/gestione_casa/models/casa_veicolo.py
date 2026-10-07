# SPDX-License-Identifier: AGPL-3.0-or-later
"""Case e veicoli: entità di primo livello, sempre condivise tra gli utenti (paragrafo 4)."""

import enum

from sqlalchemy import CheckConstraint, Index, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from gestione_casa.models.base import Base, TimestampMixin


class Casa(TimestampMixin, Base):
    __tablename__ = "casa"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    indirizzo: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text)


class TipoVeicolo(enum.StrEnum):
    AUTO = "auto"
    MOTO = "moto"
    FURGONE = "furgone"
    ALTRO = "altro"


# Testo + vincolo invece di un tipo enumerato di PostgreSQL: più semplice da estendere
_TIPI_VEICOLO = ", ".join(f"'{t.value}'" for t in TipoVeicolo)


class Veicolo(TimestampMixin, Base):
    __tablename__ = "veicolo"
    __table_args__ = (
        CheckConstraint(f"tipo IN ({_TIPI_VEICOLO})", name="tipo_valido"),
        CheckConstraint("anno BETWEEN 1900 AND 2100", name="anno_valido"),
        # Targa unica quando presente (normalizzata in maiuscolo e senza spazi dall'API, M1-12)
        Index(
            "uq_veicolo_targa",
            "targa",
            unique=True,
            postgresql_where=text("targa IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    targa: Mapped[str | None] = mapped_column(String(15))
    tipo: Mapped[str] = mapped_column(
        String(20), default=TipoVeicolo.AUTO.value, server_default=TipoVeicolo.AUTO.value
    )
    anno: Mapped[int | None] = mapped_column(SmallInteger)
