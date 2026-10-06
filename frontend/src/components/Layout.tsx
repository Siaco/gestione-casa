// SPDX-License-Identifier: AGPL-3.0-or-later
import { useTranslation } from 'react-i18next';
import { NavLink, Outlet } from 'react-router';

export function Layout() {
  const { t } = useTranslation();
  return (
    <>
      <a className="salta" href="#contenuto">
        {t('app.vaiAlContenuto')}
      </a>
      <header className="testata">
        <span className="testata__nome">{t('app.nome')}</span>
        <nav aria-label={t('app.navigazione')}>
          <NavLink to="/" end>
            {t('nav.home')}
          </NavLink>
        </nav>
      </header>
      <main id="contenuto" className="contenuto">
        <Outlet />
      </main>
    </>
  );
}
