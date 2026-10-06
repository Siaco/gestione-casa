# Gestione casa

Web app per la gestione della vita domestica di una coppia: scadenze e pagamenti con quote, spesa, faccende, manutenzioni di case e auto, contatori e consumi, calendario e note condivisi. Gira su un server domestico con Docker Compose.

Stato: **versione 0.1.0, milestone M0** (impostazione del progetto). Il progetto, le decisioni e il piano sono nel [documento iniziale](docs/documento-iniziale.md).

## Struttura

| Cartella | Contenuto |
| --- | --- |
| `backend/` | API FastAPI, modelli SQLAlchemy, migrazioni Alembic, mail, traduzioni del backend |
| `frontend/` | Interfaccia React + Vite + TypeScript, traduzioni dell'interfaccia |
| `infra/` | Docker Compose, Caddy, segreti (esclusi dal repository) |
| `docs/` | Documento iniziale, [registro delle decisioni](docs/adr/README.md), [guida allo sviluppo e al deploy](docs/sviluppo.md) |

## Avvio rapido

Sviluppo: vedi [docs/sviluppo.md](docs/sviluppo.md#sviluppo-locale).

Produzione sul server domestico:

```sh
cp .env.example .env            # e adatta i valori
# crea i segreti come descritto in infra/secrets/README.md
docker compose --env-file .env -f infra/compose.yaml up -d --build
```

L'app risponde in HTTP sulla porta 80 del server (per esempio `http://casa.lan`).

## Licenza

[GNU AGPL-3.0-or-later](LICENSE).
