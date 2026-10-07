# SPDX-License-Identifier: AGPL-3.0-or-later
"""Modelli del database. Ogni modello va importato qui perché Alembic lo veda."""

from gestione_casa.models.base import Base
from gestione_casa.models.casa_veicolo import Casa, TipoVeicolo, Veicolo
from gestione_casa.models.utente import Invito, Sessione, TokenRecuperoPassword, Utente

__all__ = [
    "Base",
    "Casa",
    "Invito",
    "Sessione",
    "TipoVeicolo",
    "TokenRecuperoPassword",
    "Utente",
    "Veicolo",
]
