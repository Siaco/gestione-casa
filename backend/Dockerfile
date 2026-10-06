# SPDX-License-Identifier: AGPL-3.0-or-later
# Immagine del backend: FastAPI + Alembic, eseguita come utente non privilegiato.
FROM python:3.14-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    TZ=Europe/Rome
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
WORKDIR /app

# Dipendenze (strato separato, ricostruito solo se cambia uv.lock)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Codice, migrazioni e traduzioni compilate
COPY alembic.ini babel.cfg ./
COPY migrations ./migrations
COPY src ./src
RUN uv sync --frozen --no-dev \
    && .venv/bin/pybabel compile -d src/gestione_casa/i18n/locale --statistics

RUN useradd --system --uid 10001 --home-dir /app gestionecasa \
    && mkdir -p /data/allegati && chown gestionecasa /data/allegati
USER gestionecasa
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

# Le migrazioni partono all'avvio; dal WP12 saranno precedute da un backup automatico.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn gestione_casa.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
