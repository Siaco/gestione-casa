# SPDX-License-Identifier: AGPL-3.0-or-later
"""Modelli del database. Ogni modello va importato qui perché Alembic lo veda."""

from gestione_casa.models.base import Base
from gestione_casa.models.utente import Utente

__all__ = ["Base", "Utente"]
