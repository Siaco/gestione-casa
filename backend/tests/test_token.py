# SPDX-License-Identifier: AGPL-3.0-or-later
from gestione_casa.sicurezza.token import corrisponde, genera_token, impronta


def test_token_casuale_e_impronta() -> None:
    a, b = genera_token(), genera_token()
    assert a.token != b.token
    assert len(a.token) >= 43  # 32 byte in base64 url-safe
    assert a.impronta == impronta(a.token)
    assert len(a.impronta) == 64
    assert a.token not in a.impronta


def test_corrispondenza() -> None:
    t = genera_token()
    assert corrisponde(t.token, t.impronta)
    assert not corrisponde(t.token + "x", t.impronta)
