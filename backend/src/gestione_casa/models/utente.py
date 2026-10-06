# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utente dell'applicazione. Autenticazione, inviti e recupero password arrivano con il WP1."""

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from gestione_casa.models.base import Base, TimestampMixin


class Utente(TimestampMixin, Base):
    __tablename__ = "utente"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    hash_password: Mapped[str] = mapped_column(String(255))
    lingua: Mapped[str] = mapped_column(String(10), default="it", server_default="it")
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
