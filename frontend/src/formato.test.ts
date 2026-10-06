// SPDX-License-Identifier: AGPL-3.0-or-later
import { formattaData, formattaImporto } from './formato';

const spazi = (s: string) => s.replace(/\s/g, ' ');

test('importi in centesimi formattati in euro', () => {
  expect(spazi(formattaImporto(123456))).toBe('1.234,56 €');
  expect(spazi(formattaImporto(-5))).toBe('-0,05 €');
});

test('importi non interi rifiutati', () => {
  expect(() => formattaImporto(1.5)).toThrow(RangeError);
});

test('date nel fuso Europe/Rome', () => {
  // 23:30 UTC del 31 marzo = 1 aprile in Italia (ora legale)
  expect(formattaData('2027-03-31T23:30:00Z')).toBe('1 aprile 2027');
});
