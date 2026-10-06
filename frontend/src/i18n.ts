// SPDX-License-Identifier: AGPL-3.0-or-later
// Traduzioni dell'interfaccia: un file JSON per lingua, chiavi stabili, formato ICU.
import i18next from 'i18next';
import ICU from 'i18next-icu';
import { initReactI18next } from 'react-i18next';

import it from './locales/it.json';

export const LINGUA_RIFERIMENTO = 'it';
export const risorse = { it: { translation: it } } as const;

void i18next
  .use(ICU)
  .use(initReactI18next)
  .init({
    resources: risorse,
    lng: LINGUA_RIFERIMENTO, // dal WP1 si usa la lingua dell'utente
    fallbackLng: LINGUA_RIFERIMENTO,
    supportedLngs: Object.keys(risorse),
    interpolation: { escapeValue: false },
    returnNull: false,
  });

export default i18next;
