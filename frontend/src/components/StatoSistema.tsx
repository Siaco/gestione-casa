// SPDX-License-Identifier: AGPL-3.0-or-later
import { useTranslation } from 'react-i18next';

import { useHealth } from '../api/health';

export function StatoSistema() {
  const { t } = useTranslation();
  const { data, isPending, isError } = useHealth();

  let testo: string;
  let classe: 'ok' | 'ko' | 'attesa';
  if (isPending) {
    testo = t('sistema.verifica');
    classe = 'attesa';
  } else if (isError) {
    testo = t('sistema.nonRaggiungibile');
    classe = 'ko';
  } else if (data.database !== 'ok') {
    testo = t('sistema.databaseKo');
    classe = 'ko';
  } else {
    testo = t('sistema.ok', { version: data.version });
    classe = 'ok';
  }

  return (
    <section className="scheda" aria-labelledby="stato-sistema">
      <h2 id="stato-sistema">{t('sistema.titolo')}</h2>
      <p className={`stato stato--${classe}`} role="status">
        {testo}
      </p>
    </section>
  );
}
