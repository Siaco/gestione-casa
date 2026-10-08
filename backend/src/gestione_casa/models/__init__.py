# SPDX-License-Identifier: AGPL-3.0-or-later
"""Modelli del database. Ogni modello va importato qui perché Alembic lo veda."""

from gestione_casa.models.base import Base
from gestione_casa.models.casa_veicolo import Casa, TipoVeicolo, Veicolo
from gestione_casa.models.tentativo import TentativoFallito
from gestione_casa.models.utente import Invito, Sessione, TokenRecuperoPassword, Utente

# Il filtro di visibilità si registra all'importazione: chi usa i modelli lo ha sempre attivo
from gestione_casa import visibilita as _visibilita  # noqa: F401  # isort: skip

__all__ = [
    "Base",
    "Casa",
    "Invito",
    "Sessione",
    "TentativoFallito",
    "TipoVeicolo",
    "TokenRecuperoPassword",
    "Utente",
    "Veicolo",
]
