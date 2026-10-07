# SPDX-License-Identifier: AGPL-3.0-or-later
# Immagine "web": frontend compilato servito da Caddy, che fa anche da reverse proxy.
# Contesto di build: la radice del repository.
FROM node:26-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY infra/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
EXPOSE 80
