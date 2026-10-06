// SPDX-License-Identifier: AGPL-3.0-or-later
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router';

export function NonTrovata() {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t('nonTrovata.titolo')}</h1>
      <Link to="/">{t('nonTrovata.tornaHome')}</Link>
    </>
  );
}
