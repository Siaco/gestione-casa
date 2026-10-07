# Sviluppo e deploy

## Prerequisiti

Postazione di sviluppo (documento iniziale, paragrafo 11.16):

- Git, Docker (su Windows: Docker Desktop con WSL2, **con il repository dentro il file system di WSL**, per esempio `~/sviluppo/gestione-casa`, non in `C:\`, per avere prestazioni adeguate);
- [uv](https://docs.astral.sh/uv/) (installa da sé Python 3.14);
- Node.js 24 LTS (file `frontend/.nvmrc`; vanno bene anche le versioni dalla 22.22);
- facoltativo: [pre-commit](https://pre-commit.com/) per gitleaks e ruff prima di ogni commit: `uvx pre-commit install`.

## Sviluppo locale

```sh
# 1. Database in container (porta 5432 solo su localhost)
printf 'sviluppo' > infra/secrets/db_password.txt
printf 'x' > infra/secrets/smtp_password.txt
printf 'x' > infra/secrets/session_secret.txt
cp .env.example .env
docker compose --env-file .env -f infra/compose.yaml -f infra/compose.dev.yaml up -d db
docker compose -f infra/compose.yaml exec db createdb -U gestione_casa gestione_casa_test

# 2. Backend (http://localhost:8000, documentazione API su /api/docs)
cd backend
uv sync
export GC_DATABASE_URL=postgresql+psycopg://gestione_casa:sviluppo@localhost:5432/gestione_casa
uv run alembic upgrade head
uv run uvicorn gestione_casa.main:app --reload

# 3. Frontend (http://localhost:5173, le chiamate /api vanno al backend)
cd frontend
npm install
npm run dev
```

## Controlli (gli stessi della pipeline)

```sh
# Backend
cd backend
uv run ruff format --check . && uv run ruff check . && uv run mypy
uv run python scripts/controlla_traduzioni.py
GC_DATABASE_URL=postgresql+psycopg://gestione_casa:sviluppo@localhost:5432/gestione_casa_test uv run pytest

# Frontend
cd frontend
npm run format:check && npm run lint && npm run typecheck && npm run i18n:check && npm test && npm run build
```

Senza `GC_DATABASE_URL` i test d'integrazione vengono saltati.

## Convenzioni

- **Lingua del codice:** i termini di dominio sono in italiano come nel documento iniziale (`Scadenza`, `proprietario_id`, `visibilita`); le API tecniche generiche (`/api/health`, campi `status`, codici di errore come `payment.shares_mismatch`) restano in inglese.
- **Testi per l'utente:** mai scritti nel codice. Frontend: chiavi stabili in `frontend/src/locales/it.json`, la regola ESLint `i18next/no-literal-string` blocca i testi letterali in JSX. Backend: restituisce solo codici di errore; i testi delle mail sono nei modelli Jinja2 con `_()`.
- **Importi:** sempre centesimi interi. **Date:** con fuso orario, `Europe/Rome`.
- **Migrazioni:** ogni modifica ai modelli richiede una migrazione (`uv run alembic revision --autogenerate -m "..."`, poi rivederla); il test `test_migrazioni.py` fallisce se modello e migrazioni non coincidono.
- **Intestazione SPDX** in ogni file sorgente: `SPDX-License-Identifier: AGPL-3.0-or-later`.
- **Rami brevi** e pull request verso `main`, con pipeline verde.

### Traduzioni del backend

```sh
cd backend
L=src/gestione_casa/i18n/locale
uv run pybabel extract -F babel.cfg -o $L/messages.pot --no-location --sort-output .
uv run pybabel update -i $L/messages.pot -d $L
```

## Attività di M0 da fare a mano

### M0-01: prerequisiti

Checklist del paragrafo 11.16 del documento iniziale: server pronto, account Gmail dedicato, repository GitHub, GitHub Project.

### Primo push su GitHub

```sh
# crea su GitHub un repository privato vuoto chiamato gestione-casa (senza README né licenza), poi:
git remote add origin git@github.com:<utente>/gestione-casa.git
git push -u origin main
```

Nelle impostazioni del repository, se disponibili per il tuo piano: *Secret scanning* e *Push protection* (Settings → Advanced Security) e protezione di `main` con pipeline verde obbligatoria. Su un repository privato di un account gratuito possono mancare: il controllo dei segreti è comunque garantito da gitleaks, nella pipeline (cronologia completa) e prima di ogni commit.

### M0-09: primo deploy sul server domestico

```sh
# sul server (Ubuntu con Docker Engine e Compose v2)
git clone git@github.com:<utente>/gestione-casa.git && cd gestione-casa
cp .env.example .env && nano .env
mkdir -p infra/secrets && chmod 700 infra/secrets
openssl rand -base64 32 | tr -d '\n' > infra/secrets/db_password.txt
openssl rand -base64 48 | tr -d '\n' > infra/secrets/session_secret.txt
printf '%s' 'PASSWORD-PER-LE-APP-GMAIL' > infra/secrets/smtp_password.txt
chmod 644 infra/secrets/*.txt
docker compose --env-file .env -f infra/compose.yaml up -d --build
docker compose -f infra/compose.yaml ps
curl http://localhost/api/health
```

Nome in rete locale: sul router assegna un IP riservato al server e, se il router lo permette, un nome DNS locale (per esempio `casa.lan`). In alternativa aggiungi il nome al file hosts dei computer; sugli smartphone si usa l'indirizzo IP.

Criterio di completamento: la pagina iniziale mostra "Tutto funziona" da computer e smartphone.

### M0-10: mail di prova

Sull'account Gmail dedicato: attiva la verifica in due passaggi, crea una password per le app e mettila in `infra/secrets/smtp_password.txt`; imposta `GC_SMTP_UTENTE` e `GC_MAIL_MITTENTE` in `.env`. Poi:

```sh
docker compose --env-file .env -f infra/compose.yaml up -d backend
docker compose -f infra/compose.yaml exec backend gestione-casa mail-prova --a tuo.indirizzo@example.com
```

Criterio di completamento: la mail arriva nella posta in arrivo e non nello spam.

### M0-11: GitHub Project

Crea un Project collegato al repository con i campi numerici **Stima (ore)** e **Ore effettive**, le etichette `WP0`…`WP14` e le milestone `M0`…`M6`. Crea le issue di M1 con la stima. Registra le ore effettive di M0 sulle issue M0-01…M0-12.
