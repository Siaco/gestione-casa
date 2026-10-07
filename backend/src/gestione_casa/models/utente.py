# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utenti e dati di accesso: inviti, recupero password, sessioni (paragrafi 8 e 9.1).

I token (inviti, recupero password, sessioni) non sono mai salvati in chiaro: nel database
c'è solo l'impronta SHA-256 (vedi ``gestione_casa.sicurezza.token``).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text, true
from sqlalchemy.orm import Mapped, mapped_column

from gestione_casa.models.base import Base, TimestampMixin

# Impronta SHA-256 in esadecimale
LUNGHEZZA_IMPRONTA = 64


class Utente(TimestampMixin, Base):
    __tablename__ = "utente"
    # Email unica senza distinzione tra maiuscole e minuscole
    __table_args__ = (Index("uq_utente_email_minuscole", text("lower(email)"), unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    hash_password: Mapped[str] = mapped_column(String(255))
    lingua: Mapped[str] = mapped_column(String(10), default="it", server_default="it")
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class Invito(Base):
    """Invito del secondo utente: link valido 7 giorni, utilizzabile una volta."""

    __tablename__ = "invito"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    creato_da_id: Mapped[int] = mapped_column(
        ForeignKey("utente.id", ondelete="CASCADE"), index=True
    )
    impronta_token: Mapped[str] = mapped_column(String(LUNGHEZZA_IMPRONTA), unique=True)
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usato_il: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TokenRecuperoPassword(Base):
    """Link di recupero password: valido 1 ora, utilizzabile una volta."""

    __tablename__ = "token_recupero_password"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utente.id", ondelete="CASCADE"), index=True)
    impronta_token: Mapped[str] = mapped_column(String(LUNGHEZZA_IMPRONTA), unique=True)
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usato_il: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Sessione(Base):
    """Sessione di accesso salvata nel database: revocabile, eliminata al logout."""

    __tablename__ = "sessione"

    id: Mapped[int] = mapped_column(primary_key=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utente.id", ondelete="CASCADE"), index=True)
    impronta_token: Mapped[str] = mapped_column(String(LUNGHEZZA_IMPRONTA), unique=True)
    creata_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ultimo_uso: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    dispositivo: Mapped[str | None] = mapped_column(String(255))
