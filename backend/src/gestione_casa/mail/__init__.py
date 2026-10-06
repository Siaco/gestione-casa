# SPDX-License-Identifier: AGPL-3.0-or-later
"""Invio delle mail tramite un livello astratto (sostituibile senza toccare il resto)."""

from gestione_casa.mail.base import Messaggio, MittenteMail
from gestione_casa.mail.render import render_mail

__all__ = ["Messaggio", "MittenteMail", "render_mail"]
