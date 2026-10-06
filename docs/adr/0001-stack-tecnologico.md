# 0001. Stack tecnologico e versioni di riferimento

- Data: 2026-10-06
- Stato: approvata

## Contesto

Applicazione per due utenti su server domestico, da far crescere fino alla gestione economica della 3.0 e da pubblicare come open source. Servono leggerezza, prestazioni adeguate e un ecosistema ampio di librerie (documento iniziale, paragrafo 3).

## Decisione

- Backend: Python con FastAPI, SQLAlchemy 2 (asincrono, driver psycopg 3) e Alembic; dipendenze gestite con uv.
- Database: PostgreSQL.
- Frontend: React con Vite, TypeScript, TanStack Query, React Router; traduzioni con i18next (formato ICU).
- Deploy: Docker Compose con Caddy come reverse proxy e server dei file statici.

Versioni di riferimento all'avvio di M0 (fissate nei file di blocco e aggiornate con Dependabot):

| Componente | Versione |
| --- | --- |
| Python | 3.14 (compatibile da 3.13) |
| PostgreSQL | 18 |
| Node.js (solo compilazione del frontend) | 24 LTS |
| FastAPI / SQLAlchemy / Alembic | 0.142 / 2.1 / 1.20 |
| React / Vite / TypeScript | 19 / 8 / 6 |
| Caddy | 2 |

## Alternative scartate

Rust (il collo di bottiglia non sarà il linguaggio), Svelte (ecosistema più ridotto), SQLite (costringerebbe a una migrazione nella 3.0).

## Conseguenze

Due linguaggi da mantenere (Python e TypeScript), compensati da tipizzazione statica in entrambi e da controlli automatici nella pipeline.
