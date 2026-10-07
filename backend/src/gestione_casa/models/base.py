# SPDX-License-Identifier: AGPL-3.0-or-later
"""Base dichiarativa e campi comuni (paragrafo 8 del documento iniziale)."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Nomi dei vincoli stabili, necessari per migrazioni Alembic ripetibili
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """Data di creazione e di ultima modifica, sempre con fuso orario."""

    creato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modificato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Visibilita(enum.StrEnum):
    CONDIVISO = "condiviso"
    PRIVATO = "privato"


class ContenutoMixin(TimestampMixin):
    """Campi di ogni entità di contenuto (paragrafo 6): proprietario e visibilità.

    Le query su queste entità sono filtrate automaticamente in base all'utente della sessione
    (``gestione_casa.visibilita``): un elemento privato è visibile e modificabile solo dal
    proprietario.
    """

    @declared_attr
    def proprietario_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("utente.id", ondelete="RESTRICT"), index=True)

    # Testo con vincolo di controllo (non un tipo enumerato di PostgreSQL), come per i veicoli
    visibilita: Mapped[Visibilita] = mapped_column(
        Enum(
            Visibilita,
            name="visibilita",
            native_enum=False,
            create_constraint=True,
            length=10,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=Visibilita.CONDIVISO,
        server_default=Visibilita.CONDIVISO.value,
    )
