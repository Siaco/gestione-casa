# 0005. Filtro di visibilità applicato dalla sessione del database

- Data: 2026-10-07
- Stato: approvata
- Issue: M1-13

## Contesto

Gli elementi privati devono essere invisibili e non modificabili dall'altro utente in ogni schermata, ricerca, mail e log (documento iniziale, paragrafo 6). Affidare il filtro ai singoli repository lascia aperta la possibilità che una query nuova lo dimentichi: è il rischio "dato privato esposto per una query dimenticata" del registro dei rischi.

## Decisione

Il filtro è applicato automaticamente dalla sessione SQLAlchemy (evento `do_orm_execute` con `with_loader_criteria`) a ogni `SELECT`, `UPDATE` e `DELETE` dell'ORM che coinvolge un'entità con `ContenutoMixin`, inclusi join, alias e caricamento delle relazioni:

`visibilita = 'condiviso' OR proprietario_id = <utente della sessione>`

La sessione ha un contesto: utente (`imposta_utente`, il caso delle richieste HTTP), sistema (`imposta_sistema`, per i job che poi filtrano per destinatario) oppure nessuno, nel qual caso non è visibile nessuna entità di contenuto (si nega in caso di errore). Il modulo è `gestione_casa/visibilita.py`.

La colonna `visibilita` è testo con vincolo di controllo, non un tipo enumerato di PostgreSQL.

## Alternative scartate

- Filtro esplicito in un repository base: più leggibile, ma una query scritta fuori dal repository lo salta.
- Row Level Security di PostgreSQL: protezione anche fuori dall'ORM, ma richiede di impostare l'utente su ogni connessione del pool e complica migrazioni e test; da riconsiderare se un giorno si useranno molte query SQL testuali.

## Conseguenze

- Le query SQL testuali (`text()`) non sono filtrate: per le entità di contenuto vanno evitate.
- Non cambiare utente nella stessa sessione senza svuotarla (`expunge_all`): gli oggetti già caricati restano nella mappa d'identità.
- Le lambda del criterio non devono chiamare funzioni né cambiare struttura in base ai valori: SQLAlchemy ne mette in cache la struttura (c'è un test di regressione).
- I test di visibilità riusabili per ogni endpoint (M1-14) si appoggiano a questo filtro.
