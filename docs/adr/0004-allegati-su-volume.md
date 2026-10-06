# 0004. Allegati su volume dedicato

- Data: 2026-10-06
- Stato: approvata

## Contesto

Quasi tutti i moduli hanno allegati (bollette, ricevute, foto). Vanno protetti dalla stessa regola di visibilità dell'elemento e inclusi nel backup.

## Decisione

File su un volume Docker dedicato (`allegati`, montato in `/data/allegati`), metadati nella tabella `Allegato`. Solo PDF, JPEG, PNG, HEIC/HEIF, al massimo 20 MB per file (configurabile con `GC_ALLEGATI_DIMENSIONE_MASSIMA_MB`). Download solo tramite il backend, che applica il controllo di visibilità.

## Alternative scartate

Allegati dentro PostgreSQL: backup unico e transazionale, ma database più pesante e backup e ripristino più lenti.

## Conseguenze

Il backup deve copiare insieme database e volume (WP12). Serve un job che rimuova i file orfani.
