# 0003. HTTP in rete locale nella 1.0

- Data: 2026-10-06
- Stato: approvata

## Contesto

Nella 1.0 l'app è accessibile solo dalla rete di casa. L'installazione come PWA richiede HTTPS (il service worker funziona solo in un contesto sicuro). Le alternative per avere HTTPS in rete locale sono un dominio proprio con certificato Let's Encrypt (sfida DNS) o una CA interna da installare su ogni dispositivo.

## Decisione

HTTP in rete locale, raggiungibile con un nome fisso (per esempio `casa.lan`). Installazione come PWA rimandata alla 2.0, insieme all'HTTPS e all'accesso dall'esterno. Caddy è configurato con `auto_https off` e risponde su qualsiasi nome sulla porta 80.

## Alternative scartate

Dominio proprio con sfida DNS (costo e configurazione anticipati alla 1.0), CA interna di Caddy (certificato da installare su ogni dispositivo e da rifare per la 2.0).

## Conseguenze

Niente PWA nella 1.0; cookie di sessione senza `Secure` (ma `HttpOnly` e `SameSite=Lax`); traffico protetto solo dalla cifratura della rete Wi-Fi. Per la 2.0 basta cambiare l'indirizzo del sito nel `Caddyfile` e togliere `auto_https off`.
