# SPDX-License-Identifier: AGPL-3.0-or-later
"""Filtro di visibilità unico (paragrafo 6 del documento iniziale, M1-13).

Ogni ``SELECT``, ``UPDATE`` e ``DELETE`` dell'ORM che coinvolge un'entità di contenuto
(``ContenutoMixin``) riceve automaticamente il criterio:

    visibilita = 'condiviso' OR proprietario_id = <utente della sessione>

Il filtro è applicato dalla sessione, non dai singoli repository: una query scritta senza
pensarci non può restituire o modificare elementi privati altrui. Vale anche per join,
alias e caricamento delle relazioni.

Contesti possibili della sessione:

- **utente**: ``imposta_utente(session, utente_id)``, il caso normale di una richiesta HTTP;
- **sistema**: ``imposta_sistema(session)``, per i job che devono vedere tutto (per esempio
  la preparazione delle mail, che poi filtrano per destinatario);
- **nessun contesto**: nessuna entità di contenuto è visibile (in caso di errore si nega).

Il filtro vale per l'ORM. Le query SQL testuali (``text()``) non sono filtrate: vanno evitate
per le entità di contenuto, o devono applicare a mano la stessa condizione.
"""

from sqlalchemy import event, false, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

from gestione_casa.models.base import ContenutoMixin, Visibilita

CHIAVE_UTENTE = "visibilita_utente_id"
CHIAVE_SISTEMA = "visibilita_sistema"


def _sessione_sincrona(session: Session | AsyncSession) -> Session:
    return session.sync_session if isinstance(session, AsyncSession) else session


def imposta_utente(session: Session | AsyncSession, utente_id: int) -> None:
    s = _sessione_sincrona(session)
    s.info.pop(CHIAVE_SISTEMA, None)
    s.info[CHIAVE_UTENTE] = utente_id


def imposta_sistema(session: Session | AsyncSession) -> None:
    s = _sessione_sincrona(session)
    s.info.pop(CHIAVE_UTENTE, None)
    s.info[CHIAVE_SISTEMA] = True


@event.listens_for(Session, "do_orm_execute")
def _applica_filtro(stato: ORMExecuteState) -> None:
    if not (stato.is_select or stato.is_update or stato.is_delete):
        return
    if stato.session.info.get(CHIAVE_SISTEMA):
        return
    utente_id: int | None = stato.session.info.get(CHIAVE_UTENTE)
    # Due lambda distinte e senza chiamate a funzioni: SQLAlchemy mette in cache la struttura
    # della lambda e tratta solo le variabili catturate (utente_id) come parametri.
    if utente_id is None:
        criterio = with_loader_criteria(ContenutoMixin, lambda cls: false(), include_aliases=True)
    else:
        criterio = with_loader_criteria(
            ContenutoMixin,
            lambda cls: or_(
                cls.visibilita == Visibilita.CONDIVISO, cls.proprietario_id == utente_id
            ),
            include_aliases=True,
        )
    stato.statement = stato.statement.options(criterio)
