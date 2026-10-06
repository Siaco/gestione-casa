// SPDX-License-Identifier: AGPL-3.0-or-later
import { useTranslation } from 'react-i18next';

import { StatoSistema } from '../components/StatoSistema';

export function Home() {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t('home.titolo')}</h1>
      <p>{t('home.introduzione')}</p>
      <StatoSistema />
    </>
  );
}
