// SPDX-License-Identifier: AGPL-3.0-or-later
// Formattazione di importi e date con Intl. Importi sempre in centesimi interi (paragrafo 8).

export const FUSO_ORARIO = 'Europe/Rome';
export const VALUTA = 'EUR';

export function formattaImporto(centesimi: number, lingua = 'it'): string {
  if (!Number.isInteger(centesimi)) {
    throw new RangeError('Gli importi devono essere centesimi interi');
  }
  return new Intl.NumberFormat(lingua, {
    style: 'currency',
    currency: VALUTA,
    useGrouping: 'always', // CLDR italiano non separa le migliaia sotto 10.000
  }).format(centesimi / 100);
}

export function formattaData(data: Date | string, lingua = 'it'): string {
  return new Intl.DateTimeFormat(lingua, { dateStyle: 'long', timeZone: FUSO_ORARIO }).format(
    typeof data === 'string' ? new Date(data) : data,
  );
}
