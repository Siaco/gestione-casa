# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tentativi falliti di accesso, per limitare gli attacchi a forza bruta (M1-05)."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from gestione_casa.models.base import Base


class TentativoFallito(Base):
    __tablename__ = "tentativo_fallito"
    __table_args__ = (Index("ix_tentativo_fallito_ricerca", "ambito", "chiave", "avvenuto_il"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ambito: Mapped[str] = mapped_column(String(20))
    """Operazione limitata: login, recupero_password, invito."""
    chiave: Mapped[str] = mapped_column(String(300))
    """Chi tenta: "ip:<indirizzo>" oppure "email:<indirizzo normalizzato>"."""
    avvenuto_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
