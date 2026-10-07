// SPDX-License-Identifier: AGPL-3.0-or-later
import i18n from './i18n';

test('errori del backend tradotti con i parametri (formato ICU)', () => {
  expect(i18n.t('errori.auth.password_too_short', { min: 12 })).toBe(
    'La password deve avere almeno 12 caratteri',
  );
});

test('codice di errore sconosciuto: si ripiega sulla chiave', () => {
  expect(i18n.exists('errori.codice.inesistente')).toBe(false);
});
