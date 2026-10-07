# SPDX-License-Identifier: AGPL-3.0-or-later
"""Vincoli del database su utenti, token, sessioni, case e veicoli (M1-01)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gestione_casa.config import get_settings
from gestione_casa.models import Casa, Invito, Sessione, TokenRecuperoPassword, Utente, Veicolo
from gestione_casa.sicurezza.token import genera_token


@pytest.fixture
def db(database: None) -> Iterator[Session]:
    """Sessione sincrona sul database di test (driver psycopg anche in modalità sincrona)."""
    engine = create_engine(get_settings().url_database())
    with Session(engine) as s:
        yield s
    engine.dispose()


def _utente(email: str = "camillo@example.com") -> Utente:
    return Utente(nome="Camillo", email=email, hash_password="x")


def test_email_unica_senza_maiuscole(db: Session) -> None:
    db.add(_utente("Camillo@Example.com"))
    db.commit()
    db.add(_utente("camillo@example.COM"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_impronte_dei_token_uniche(db: Session) -> None:
    u = _utente()
    db.add(u)
    db.flush()
    t = genera_token()
    domani = datetime.now(UTC) + timedelta(days=1)
    db.add(Sessione(utente_id=u.id, impronta_token=t.impronta, scade_il=domani))
    db.add(Sessione(utente_id=u.id, impronta_token=t.impronta, scade_il=domani))
    with pytest.raises(IntegrityError):
        db.commit()


def test_eliminare_un_utente_elimina_sessioni_inviti_e_token(db: Session) -> None:
    u = _utente()
    db.add(u)
    db.flush()
    scadenza = datetime.now(UTC) + timedelta(hours=1)
    db.add_all(
        [
            Sessione(utente_id=u.id, impronta_token=genera_token().impronta, scade_il=scadenza),
            Invito(
                email="aurora@example.com",
                creato_da_id=u.id,
                impronta_token=genera_token().impronta,
                scade_il=scadenza,
            ),
            TokenRecuperoPassword(
                utente_id=u.id, impronta_token=genera_token().impronta, scade_il=scadenza
            ),
        ]
    )
    db.commit()
    db.execute(delete(Utente).where(Utente.id == u.id))
    db.commit()
    for modello in (Sessione, Invito, TokenRecuperoPassword):
        assert db.scalars(select(modello)).all() == []


def test_valori_predefiniti_utente_e_casa(db: Session) -> None:
    u = _utente()
    casa = Casa(nome="Casa di Frosinone")
    db.add_all([u, casa])
    db.commit()
    db.refresh(u)
    db.refresh(casa)
    assert u.lingua == "it" and u.attivo is True
    assert u.creato_il.tzinfo is not None
    assert casa.indirizzo is None


def test_veicolo_targa_unica_se_presente(db: Session) -> None:
    db.add_all([Veicolo(nome="Bici"), Veicolo(nome="Bici 2")])  # targa assente: ammessa più volte
    db.add(Veicolo(nome="Auto", targa="AB123CD"))
    db.commit()
    db.add(Veicolo(nome="Altra auto", targa="AB123CD"))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize(
    ("campi", "vincolo"),
    [({"tipo": "astronave"}, "ck_veicolo_tipo_valido"), ({"anno": 1800}, "ck_veicolo_anno_valido")],
)
def test_veicolo_valori_non_validi(db: Session, campi: dict[str, object], vincolo: str) -> None:
    db.add(Veicolo(nome="Prova", **campi))
    with pytest.raises(IntegrityError, match=vincolo):
        db.commit()
