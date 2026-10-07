# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from argon2 import PasswordHasher

from gestione_casa.errors import AppError
from gestione_casa.sicurezza.password import (
    LUNGHEZZA_MASSIMA,
    LUNGHEZZA_MINIMA,
    calcola_hash,
    valida_password,
    verifica_fittizia,
    verifica_password,
)


def test_hash_argon2id_e_verifica() -> None:
    h = calcola_hash("una password lunga")
    assert h.startswith("$argon2id$")
    assert "una password lunga" not in h
    assert verifica_password(h, "una password lunga") == (True, None)
    assert verifica_password(h, "una password diversa").valida is False


def test_hash_diversi_per_la_stessa_password() -> None:
    assert calcola_hash("una password lunga") != calcola_hash("una password lunga")


def test_normalizzazione_unicode() -> None:
    composta, precomposta = "caffé al mattino!", "caffé al mattino!"
    assert verifica_password(calcola_hash(composta), precomposta).valida


def test_hash_non_valido_non_solleva_eccezioni() -> None:
    assert verifica_password("non-un-hash", "qualsiasi password").valida is False


def test_hash_da_aggiornare_se_cambiano_i_parametri() -> None:
    vecchio = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(
        "una password lunga"
    )
    esito = verifica_password(vecchio, "una password lunga")
    assert esito.valida
    assert esito.nuovo_hash is not None and esito.nuovo_hash != vecchio
    assert verifica_password(esito.nuovo_hash, "una password lunga") == (True, None)


def test_verifica_fittizia() -> None:
    verifica_fittizia("qualsiasi password")  # non solleva e non restituisce nulla


@pytest.mark.parametrize(
    ("password", "email", "codice"),
    [
        ("a" * (LUNGHEZZA_MINIMA - 1), None, "auth.password_too_short"),
        ("a" * (LUNGHEZZA_MASSIMA + 1), None, "auth.password_too_long"),
        ("Camillo@Example.com", "camillo@example.com", "auth.password_equals_email"),
        (" camillo@example.com ", "camillo@example.com", "auth.password_equals_email"),
    ],
)
def test_password_non_valide(password: str, email: str | None, codice: str) -> None:
    with pytest.raises(AppError) as errore:
        valida_password(password, email)
    assert errore.value.code == codice
    assert errore.value.status_code == 422


@pytest.mark.parametrize(
    "password", ["a" * LUNGHEZZA_MINIMA, "solo lettere minuscole", "1234567890ab"]
)
def test_password_valide_senza_regole_di_composizione(password: str) -> None:
    valida_password(password, "camillo@example.com")
