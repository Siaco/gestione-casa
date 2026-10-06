# Segreti

Questa cartella contiene i segreti usati da Docker Compose. Tutto tranne questo file è escluso dal repository.

Crea questi file, ciascuno con il solo valore e senza a capo finale:

| File | Contenuto |
| --- | --- |
| `db_password.txt` | Password dell'utente PostgreSQL dell'app |
| `smtp_password.txt` | Password per le app dell'account Gmail dedicato |
| `session_secret.txt` | Chiave casuale per le sessioni |

Per generare valori casuali:

```sh
openssl rand -base64 32 | tr -d '\n' > infra/secrets/db_password.txt
openssl rand -base64 48 | tr -d '\n' > infra/secrets/session_secret.txt
chmod 700 infra/secrets
chmod 644 infra/secrets/*.txt
```

I file sono leggibili (644) perché il backend gira nel container con un utente non privilegiato (uid 10001); la protezione sul server la dà la cartella, accessibile solo al proprietario (700).
