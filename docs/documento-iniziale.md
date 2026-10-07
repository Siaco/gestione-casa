# Web app per la gestione casalinga: documento iniziale

Versione del documento: 0.8 · 7 ottobre 2026 · Stato: bozza condivisa, decisioni di progetto

## 1. Obiettivo e perimetro

Applicazione web per la gestione della vita domestica di due persone (Camillo e Aurora): scadenze e pagamenti, spesa, faccende, manutenzioni di case e auto, contatori e consumi, calendario e note condivisi.

- **Utenti:** due, con account separati.
- **Ambiente:** server domestico Ubuntu in rete locale.
- **Lingua e valuta:** interfaccia in italiano, predisposta alla traduzione; solo euro.
- **Dispositivi:** web app responsive, usabile da computer e smartphone tramite browser. L'installazione come PWA è rimandata alla 2.0, perché richiede HTTPS (paragrafo 9).

## 2. Roadmap

| Versione | Contenuto |
| --- | --- |
| **1.0** | Tutti i moduli del paragrafo 4, accesso solo da rete locale, notifiche via mail |
| **2.0** | Accesso dall'esterno (HTTPS, hardening, 2FA), installazione come PWA, notifiche push |
| **3.0** | Gestione economica completa: spese, budget, saldo tra utenti, report, importazione estratti conto |

La 1.0 è predisposta per le versioni successive (campo `canale` nelle notifiche, quote dei pagamenti già registrate, livello di invio mail sostituibile).

## 3. Stack tecnologico

| Livello | Scelta | Motivazione |
| --- | --- | --- |
| Backend | Python + FastAPI | Leggero e veloce, ecosistema molto ampio per upgrade futuri |
| ORM e migrazioni | SQLAlchemy 2 + Alembic | Standard consolidato |
| Database | PostgreSQL | Pronto per report e dati economici della 3.0 |
| Frontend | React + Vite + TanStack Query; responsive, PWA nella 2.0 | Massimo ecosistema di librerie (calendario, grafici, componenti) |
| Job schedulati | APScheduler nel processo backend | Sufficiente per le mail; Celery o arq solo se servirà carico pesante |
| Mail | SMTP Gmail con password per le app | Account Gmail dedicato; livello di invio astratto |
| Deploy | Docker Compose + reverse proxy (Caddy o Traefik) | Già pronto per l'esposizione esterna della 2.0 |
| Autenticazione | Sessioni con cookie HttpOnly, hash argon2 | Predisposta a ruoli e 2FA nella 2.0 |
| Tempo reale | WebSocket | Aggiornamento live della lista della spesa |
| Traduzione | react-i18next (frontend), Jinja2 e Babel (mail e testi del backend) | Interfaccia predisposta a più lingue fin dall'inizio |
| Backup | restic (cifrato), destinazione configurabile | Locale, condivisione di rete montata (SMB/NFS), SFTP o archivio compatibile S3, a scelta dell'amministratore di sistema |

Note: Rust è stato scartato perché il collo di bottiglia non sarà il linguaggio; Svelte è stato scartato per l'ecosistema più ridotto; SQLite basterebbe per due utenti ma costringerebbe a una migrazione nella 3.0.

## 4. Moduli della versione 1.0

1. **Scadenze e pagamenti:** memo con ricorrenza (RRULE), importo previsto, categoria, stato, allegati PDF.
2. **Spesa:** liste condivise in tempo reale, reparti, articoli ricorrenti, storico.
3. **Faccende domestiche:** attività ricorrenti con assegnatario o rotazione e stato di completamento.
4. **Manutenzioni di case e auto:** scadenze a tempo e/o a chilometraggio, storico interventi con costo e fornitore.
5. **Contatori e consumi:** luce, gas, acqua; **letture inserite a mano** leggendo la bolletta, PDF allegato, grafici dei consumi. Nessuna estrazione automatica (eventuale upgrade futuro).
6. **Calendario condiviso:** vista mese e settimana, integra scadenze, manutenzioni e faccende, eventi manuali, esportazione ICS.
7. **Note condivise:** markdown, checklist, note fissate in alto.
8. **Notifiche mail:** livelli di urgenza con cadenze diverse (paragrafo 5).
9. **Trasversali:** dashboard "oggi / questa settimana", ricerca globale, log delle attività, backup automatico del database.

### Multi-casa e multi-auto

`Casa` e `Veicolo` sono entità di primo livello e se ne possono gestire quante si vuole fin da subito. Contatori, manutenzioni, scadenze e faccende possono essere collegati a una casa, a un veicolo o a nessuno. Un selettore di contesto filtra l'interfaccia. Case e veicoli sono sempre condivisi.

## 5. Notifiche mail

| Contenuto | Cadenza predefinita |
| --- | --- |
| Scadenza critica (pagamento, revisione) | 7 giorni prima, 1 giorno prima, giorno stesso |
| Scadenza ordinaria (abbonamenti, manutenzioni) | 14 e 3 giorni prima |
| Faccende e spesa | digest quotidiano al mattino |
| Riepilogo generale | digest settimanale (domenica sera) |
| Lettura contatore mancante | promemoria a inizio periodo |
| Aggiornamento km del veicolo | promemoria mensile (paragrafo 8.2) |

Le cadenze sono configurabili per elemento e per utente. Gli orari usano esplicitamente il fuso `Europe/Rome`. Ogni notifica è registrata (tipo, destinatario, canale, stato di invio) per evitare doppi invii.

## 6. Visibilità: condiviso e personale

Ogni entità di contenuto (scadenza, nota, evento, faccenda, lista della spesa, manutenzione, contatore) ha:

- `proprietario_id`
- `visibilita`: `condiviso` oppure `privato`

Un elemento privato è visibile e modificabile solo dal proprietario.

- **Applicazione della regola:** a livello di query nel backend, con un unico filtro riusato da tutti i repository, non solo nell'interfaccia.
- **Calendario:** gli **eventi privati** compaiono all'altro utente come **"Occupato"**, con la fascia oraria e senza titolo né dettagli. Scadenze, faccende e note private non compaiono all'altro utente (confermato).
- **Mail:** le notifiche di un elemento privato vanno solo al proprietario; i digest dell'altro non ne contengono nemmeno il titolo.
- **Ricerca globale e log attività:** stesso filtro.
- **Allegati:** ereditano la visibilità dell'elemento.

## 7. Pagamenti e quote

| Entità | Campi |
| --- | --- |
| `Pagamento` | scadenza, data effettiva, importo reale (centesimi), `pagato_da_id` |
| `QuotaPagamento` | pagamento, utente, importo dovuto (centesimi) |

**Regola predefinita: ripartizione proporzionale allo stipendio netto di ciascuno.**

- Ogni utente ha uno storico `RedditoNetto` (utente, importo mensile netto in centesimi, valido dal), così una variazione di stipendio non altera i pagamenti passati.
- Alla creazione di un pagamento, la quota di ciascuno è `importo × reddito_utente / somma_redditi`, calcolata sui redditi validi alla data del pagamento e poi **congelata**.
- Arrotondamento: le quote sono in centesimi interi; l'ultimo utente riceve il resto, così la somma coincide sempre con l'importo reale (vincolo verificato nel backend).
- Ogni `Scadenza` può sovrascrivere la ripartizione predefinita (parti uguali, 100% a uno, percentuali personalizzate).
- I pagamenti su elementi privati hanno una sola quota, 100% al proprietario.
- **Visibilità dello stipendio: decide ciascun utente.** Ogni utente imposta se condividere il proprio stipendio netto con l'altro (campo `visibile_al_partner` in `RedditoNetto`). Il valore predefinito è **non condiviso** (confermato). In ogni caso il sistema lo usa per il calcolo delle quote.
- Limite da conoscere: con due soli utenti, le quote mostrate rivelano la proporzione tra i due stipendi anche se il valore assoluto resta nascosto. Se si vuole nascondere anche la proporzione, serve una ripartizione manuale (per esempio parti uguali) a scelta di chi la imposta.
- Il calcolo del saldo tra utenti (chi deve a chi) non è nella 1.0, ma i dati registrati sono già sufficienti per la 3.0.

## 8. Modello dati (nucleo)

| Entità | Campi principali |
| --- | --- |
| `Utente` | nome, email, hash password, lingua (predefinita `it`), attivo, creato il |
| `Invito` | email, creato da, impronta del token, scadenza, usato il |
| `TokenRecuperoPassword` | utente, impronta del token, scadenza (1 ora), usato il |
| `Sessione` | utente, impronta del token, creata il, scade il, ultimo uso, dispositivo (user agent); revocabile, eliminata al logout e al cambio password |
| `RedditoNetto` | utente, importo mensile (centesimi), valido dal, visibile al partner (sì/no) |
| `Casa` | nome, indirizzo, note |
| `Veicolo` | nome, targa (unica se presente), tipo (auto, moto, furgone, altro), anno, km attuali (derivati dall'ultima `LetturaKm`) |
| `LetturaKm` | veicolo, data, km, origine (manuale / intervento) |
| `Categoria` | ambito (scadenza / reparto della spesa), nome (chiave di traduzione per le voci predefinite), origine (predefinito/personalizzato), attivo, ordine |
| `Scadenza` | titolo, categoria, importo previsto, data di inizio, ricorrenza (RRULE), stato, ripartizione predefinita, casa/veicolo opzionali, allegati |
| `EccezioneOccorrenza` | elemento ricorrente (scadenza, faccenda o evento), data originaria, nuova data oppure annullata |
| `Pagamento` / `QuotaPagamento` | vedi paragrafo 7; il pagamento ha anche `scadenza_id` e `data_occorrenza` (paragrafo 8.1) |
| `TipoManutenzione` | nome (chiave di traduzione per le voci predefinite), ambito (casa/veicolo), classe (ordinaria/straordinaria), categoria, intervallo predefinito a tempo e/o km, promemoria predefiniti, note, origine (predefinito/personalizzato), attivo, modificato dall'utente, archiviato il (vedi Appendice A) |
| `Manutenzione` | casa/veicolo, tipo, intervallo a tempo e/o km (sovrascrive quello predefinito), ultimo intervento, prossima scadenza calcolata |
| `Intervento` | manutenzione o tipo, data, km, costo, fornitore, note, allegati; per la classe straordinaria anche motivo, preventivo, importo finale, garanzia fino al, detraibile (sì/no) |
| `Contatore` | casa, tipo, unità di misura, matricola |
| `Lettura` | contatore, data, valore, periodo di riferimento, importo bolletta opzionale |
| `ListaSpesa` / `ArticoloSpesa` | nome, quantità, reparto (`Categoria`), spuntato, ricorrente |
| `Faccenda` | titolo, casa, ricorrenza, modalità di assegnazione (fissa / rotazione), assegnatario fisso, ordine di rotazione (elenco di utenti), posizione corrente nella rotazione |
| `CompletamentoFaccenda` | faccenda, data occorrenza, completata da, completata il |
| `Evento` | titolo, inizio/fine, partecipanti, luogo, ricorrenza |
| `Nota` | titolo, markdown, fissata, casa opzionale |
| `Allegato` | entità collegata (tipo e id), nome originale, tipo MIME, dimensione, impronta SHA-256, percorso nel volume, caricato da, caricato il |
| `PreferenzaNotifica` | utente, tipo di notifica o singolo elemento (opzionale), anticipi in giorni, orario, canale, attiva |
| `Notifica` | tipo, destinatario, canale, riferimento, data occorrenza, stato di invio |
| `LogAttivita` | utente, azione, tipo ed id dell'entità, data e ora, riepilogo senza dati sensibili |

Convenzioni: importi in centesimi (interi, mai float); ricorrenze con RRULE (`python-dateutil`), occorrenze generate su finestra mobile; tutte le entità di contenuto con `proprietario_id`, `visibilita`, `creato_il`, `modificato_il`. Le entità tecniche (`Allegato`, `LogAttivita`, `Notifica`) ereditano la visibilità dell'elemento a cui si riferiscono.

### 8.1 Occorrenze delle ricorrenze

Le occorrenze di scadenze, faccende ed eventi non sono salvate: si calcolano dalla RRULE su una finestra mobile. Per collegare un fatto a una singola occorrenza si usa la **data originaria dell'occorrenza** come chiave (come `RECURRENCE-ID` nello standard iCalendar).

- `Pagamento` ha `scadenza_id` + `data_occorrenza`, con vincolo di unicità: un'occorrenza risulta pagata se esiste il pagamento.
- `CompletamentoFaccenda` e `Notifica` usano la stessa chiave; il vincolo di unicità su `Notifica` (tipo, destinatario, riferimento, data occorrenza, anticipo) impedisce i doppi invii.
- Spostare o annullare una singola occorrenza crea una `EccezioneOccorrenza`, senza toccare la regola.
- Modificare la regola di una serie la divide: la serie vecchia termina il giorno prima della modifica (`UNTIL`) e ne nasce una nuova. Così pagamenti e completamenti passati restano collegati alle occorrenze giuste.

### 8.2 Chilometraggio e manutenzioni a km

- I km si inseriscono a mano (`LetturaKm`) e vengono registrati anche da ogni `Intervento` che riporta i km. I km attuali del veicolo sono quelli dell'ultima lettura.
- Promemoria mensile di aggiornamento dei km (stesso meccanismo del promemoria per le letture dei contatori), configurabile per veicolo.
- **Stima della data di scadenza a km:** percorrenza media giornaliera calcolata sulle letture degli ultimi 12 mesi (almeno due letture distanti almeno 30 giorni). Data stimata = oggi + km mancanti / media giornaliera.
- Se una manutenzione ha sia un intervallo a tempo sia uno a km, vale la **prima delle due date**.
- Senza dati sufficienti per la stima, si usa solo l'intervallo a tempo e l'interfaccia mostra i km mancanti senza data.
- Le mail delle scadenze a km usano la data stimata, ricalcolata a ogni nuova lettura.

### 8.3 Allegati

- File salvati su un **volume Docker dedicato**, con i metadati nella tabella `Allegato`; nome sul disco generato dal sistema (non quello originale).
- Formati ammessi: PDF, JPEG, PNG, HEIC/HEIF; tipo verificato sul contenuto del file, non solo sull'estensione. Limite di **20 MB per file**, configurabile.
- Download solo tramite il backend, che applica il controllo di visibilità; il reverse proxy non serve mai direttamente la cartella.
- Eliminando un elemento si eliminano i suoi allegati; un job settimanale rimuove i file orfani.
- Il volume è incluso nel backup restic insieme al database.

## 9. Sicurezza e operatività

- Segreti (password per le app Gmail, chiavi di sessione) in Docker secrets, mai nel repository.
- Account Gmail dedicato all'app, con verifica in due passaggi e password per le app.
- Backup automatico giornaliero del database e degli allegati, con rotazione e destinazione scelta dall'amministratore di sistema (paragrafo 11.11).
- Accesso limitato alla rete locale nella 1.0; l'esposizione esterna richiede il lavoro di hardening della 2.0.
- **HTTP in rete locale nella 1.0.** L'app è raggiungibile in HTTP tramite il nome che il router assegna al server in rete locale: `zeus.fritz.box` (FRITZ!Box, indirizzo IP 192.168.178.51; verificato in M0). Conseguenze accettate: niente installazione come PWA, cookie di sessione senza attributo `Secure` (ma con `HttpOnly` e `SameSite=Lax`), traffico in chiaro protetto solo dalla cifratura della rete Wi-Fi. L'HTTPS arriva con la 2.0; la configurazione del reverse proxy è già predisposta per attivarlo.

### 9.1 Account: primo avvio, inviti e recupero password

- **Primo avvio guidato:** se il database non contiene utenti, l'app mostra una schermata di configurazione che crea il primo utente. Per evitare che qualcun altro sulla rete la usi prima di te, la schermata chiede un codice monouso scritto nei log del server all'avvio. Dopo la creazione del primo utente la schermata si disattiva.
- **Invito del secondo utente:** il primo utente invia un invito via mail con un link valido 7 giorni; chi lo apre sceglie nome e password. Numero massimo di utenti configurabile, predefinito 2. Non esiste registrazione libera.
- **Recupero password:** link via mail valido 1 ora e utilizzabile una volta sola, con risposta identica sia per email esistenti sia inesistenti. Il link funziona solo dalla rete locale nella 1.0.
- **Soluzione di emergenza:** un comando sul server reimposta la password di un utente, nel caso in cui l'invio delle mail non funzioni.
- Token di inviti e recuperi salvati solo come impronta (hash), mai in chiaro.

## 10. Punti ancora aperti

1. **Schermata di amministrazione nell'app:** la destinazione del backup si sceglie nella configurazione del server, senza un ruolo di amministratore dentro l'app. Per la 1.0 la ritengo sufficiente; da confermare se serve anche una schermata dedicata.
2. Adattamento del catalogo di manutenzione (Appendice A) ai casi reali, anche dopo il rilascio grazie alla modularità.
3. Seconda copia del backup fuori casa: tecnicamente già configurabile, resta da decidere se e quando attivarla.

Decisioni chiuse: calendario (solo gli eventi privati compaiono come "Occupato"); visibilità dello stipendio rimessa alla scelta di ciascun utente, con valore predefinito "non condiviso"; catalogo delle tipologie di manutenzione definito e modulare (Appendice A); disponibilità di sviluppo di circa 16 ore a settimana; codice e integrazione continua su GitHub; distribuzione open source prevista al termine della 3.0; backup con destinazione scelta dall'amministratore di sistema (predefinita: copia locale); avvio del progetto il 6 ottobre 2026; licenza AGPL-3.0-or-later; predisposizione alla traduzione fin dall'inizio; funzionalità Could della 1.0 come obiettivo non vincolante per il rilascio; WP14 assegnato alla milestone M6; HTTP in rete locale e installazione PWA rimandata alla 2.0; primo avvio guidato con invito del secondo utente e recupero password via mail; allegati su volume dedicato (PDF e immagini, massimo 20 MB); invio mail con account Gmail dedicato e password per le app, dopo il confronto con i servizi transazionali (da rivalutare con il dominio della 2.0); nome in rete locale `zeus.fritz.box`; sessioni salvate nel database (revocabili).

---

## 11. Pianificazione tecnica e di progetto

Le stime di questo capitolo sono indicative (incertezza di circa ±30%) e vanno riviste dopo la prima milestone.

### 11.1 Obiettivi e criteri di successo

| Obiettivo | Criterio misurabile |
| --- | --- |
| Nessuna scadenza dimenticata | 100% delle scadenze generano le mail previste, verificato dal registro `Notifica` |
| Uso quotidiano da due persone | Dashboard "oggi" caricata in meno di 2 secondi sulla rete locale |
| Dati privati realmente privati | 0 casi di elementi privati visibili all'altro utente nei test automatici |
| Quote corrette | Somma delle quote uguale all'importo reale in ogni pagamento (test su casi limite) |
| Dati al sicuro | Ripristino da backup provato con successo prima del rilascio |

### 11.2 Ambito della versione 1.0

| Incluso | Escluso (rimandato) |
| --- | --- |
| I 9 moduli del paragrafo 4 | Accesso dall'esterno, 2FA, notifiche push (2.0) |
| Mail Gmail con cadenze per urgenza | Spese, budget, saldo, report, estratti conto (3.0) |
| Visibilità condiviso/privato, quote per pagamento | Estrazione automatica da PDF delle bollette |
| Catalogo manutenzioni modulare, interfaccia responsive, backup, predisposizione alla traduzione | Installazione come PWA e HTTPS (2.0) |
| Primo avvio guidato, invito del secondo utente, recupero password via mail | Integrazioni con assistenti vocali e dispositivi domotici; lingue diverse dall'italiano; valute diverse dall'euro |

### 11.3 Ruoli e responsabilità

| Ruolo | Chi | Responsabilità |
| --- | --- | --- |
| Sponsor e product owner | Camillo | Priorità, decisioni di ambito, accettazione finale |
| Architetto e sviluppatore | Camillo, con eventuale assistenza di strumenti di sviluppo assistito | Progetto tecnico, codice, deploy |
| Amministratore di sistema | chi gestisce il server (oggi Camillo) | Installazione, configurazione, destinazione del backup, aggiornamenti, segreti |
| Utente chiave e collaudatore | Aurora | Prova dei flussi reali, feedback di usabilità, accettazione per i moduli condivisi |

### 11.4 Vincoli, assunzioni e dipendenze

- **Vincoli:** server domestico Ubuntu con Docker; solo italiano ed euro; nessun budget per licenze o servizi a pagamento; sviluppo nel tempo libero.
- **Assunzioni:** due soli utenti; rete locale stabile; un account Gmail dedicato con password per le app; il server resta acceso 24 ore su 24.
- **Dipendenze esterne:** Gmail (SMTP) per le mail; una destinazione di backup scelta dall'amministratore di sistema (predefinita: supporto locale separato dal server).

### 11.5 Requisiti non funzionali (proposti)

| Area | Obiettivo |
| --- | --- |
| Prestazioni | Risposta API al 95° percentile sotto 300 ms in rete locale |
| Disponibilità | Riavvio automatico dei container; tempo di ripristino (RTO) fino a 4 ore |
| Dati | Perdita massima tollerata (RPO) di 24 ore, con backup giornaliero |
| Sicurezza | Hash argon2, cookie HttpOnly e SameSite, protezione CSRF, limitazione dei tentativi di accesso, segreti fuori dal repository; HTTP solo in rete locale nella 1.0 (paragrafo 9) |
| Usabilità | Uso comodo da smartphone, interfaccia in italiano, azioni frequenti in al massimo 3 tocchi |
| Manutenibilità | Tipizzazione (mypy, TypeScript), formattazione e analisi statica automatiche, migrazioni versionate |
| Portabilità | Tutto in Docker Compose, riavviabile su un altro host con backup e file di configurazione |

### 11.6 Struttura del lavoro e stima dell'impegno

| Pacchetto di lavoro | Stima (giorni-persona) |
| --- | --- |
| WP0 Impostazione: repository, Docker Compose, CI, schema iniziale, infrastruttura di traduzione | 4-6 |
| WP1 Fondamenta: primo avvio guidato, inviti, autenticazione e recupero password, utenti (con lingua), case e veicoli, visibilità condiviso/privato | 8-10 |
| WP2 Scadenze, pagamenti, quote proporzionali, ricorrenze | 8-10 |
| WP3 Notifiche mail (modelli traducibili) e job schedulati | 6-8 |
| WP4 Manutenzioni e catalogo modulare | 6-8 |
| WP5 Contatori e consumi con grafici | 4-6 |
| WP6 Lista della spesa in tempo reale | 4-6 |
| WP7 Faccende domestiche | 3-4 |
| WP8 Calendario condiviso ed esportazione ICS | 6-8 |
| WP9 Note condivise | 2-3 |
| WP10 Dashboard, ricerca globale, log attività | 5-7 |
| WP11 Rifinitura dell'interfaccia mobile (responsive) | 1-2 |
| WP12 Sicurezza, backup, test di ripristino, deploy | 6-8 |
| WP13 Collaudo con Aurora, correzioni, documentazione d'uso | 3-4 |
| WP14 Traduzione trasversale: stringhe estratte nei moduli, controlli automatici dei testi mancanti | 2-3 |
| **Totale** | **68-93** (più circa 20% di riserva) |

La durata in calendario è calcolata nel paragrafo 11.7 sulla disponibilità di circa 16 ore a settimana. Le stime ipotizzano sviluppo senza assistenza; con strumenti di sviluppo assistito l'impegno può calare, ma non lo scalo dalle stime finché non c'è un dato misurato sulla prima milestone.

### 11.7 Milestone e ordine di rilascio

| Milestone | Contenuto | Valore consegnato |
| --- | --- | --- |
| M0 | WP0 | Ambiente di sviluppo e deploy funzionanti |
| M1 | WP1 | Accesso per due utenti, case e veicoli, privacy dei dati |
| M2 | WP2 + WP3 | **Primo valore reale:** scadenze, pagamenti con quote e mail di promemoria |
| M3 | WP4 + WP5 | Manutenzioni e consumi |
| M4 | WP6 + WP7 | Spesa e faccende |
| M5 | WP8 + WP9 + WP10 + WP11 | Calendario, note, dashboard, uso da smartphone |
| M6 | WP12 + WP13 + WP14 | **Rilascio 1.0** dopo collaudo e verifica completa delle traduzioni |

L'infrastruttura di traduzione è impostata in WP0 e ogni modulo nasce con le stringhe nei file di lingua; WP14 (estrazione residua e controlli automatici completi) chiude il lavoro in M6.

Il rilascio è incrementale: dopo M2 l'app è già utilizzabile in casa, e questo permette di raccogliere feedback reale prima del resto.

**Durata stimata a 16 ore a settimana** (2 giorni-persona a settimana, ore effettive di sviluppo). Le settimane sono contate dall'avvio (6 ottobre 2026) e sono cumulative; tra parentesi le date indicative.

| Milestone | Giorni-persona | Fine, scenario ottimistico | Fine, scenario prudente |
| --- | --- | --- | --- |
| M0 | 4-6 | settimana 2 (20 ott 2026) | settimana 3 (27 ott 2026) |
| M1 | 8-10 | settimana 6 (17 nov 2026) | settimana 8 (1 dic 2026) |
| M2 | 14-18 | settimana 13 (5 gen 2027) | settimana 17 (2 feb 2027) |
| M3 | 10-14 | settimana 18 (9 feb 2027) | settimana 24 (23 mar 2027) |
| M4 | 7-10 | settimana 21,5 (5 mar 2027) | settimana 29 (27 apr 2027) |
| M5 | 14-20 | settimana 28,5 (24 apr 2027) | settimana 39 (6 lug 2027) |
| M6 (1.0) | 11-15 | settimana 34 (1 giu 2027) | settimana 46,5 (28 ago 2027) |
| **Totale** | **68-93** |  |  |
| M6 con riserva del 20% |  |  | settimana 56 (2 nov 2027) |

I giorni-persona di ogni milestone sono la somma esatta dei pacchetti di lavoro che contiene (paragrafo 11.6). Le date sono indicative e non considerano ferie e periodi di pausa. La 1.0 arriverebbe tra giugno e agosto 2027, e con tutta la riserva a inizio novembre 2027; il primo valore reale (M2) tra inizio gennaio e inizio febbraio 2027. Rispetto alla versione 0.6, il WP1 cresce di un giorno-persona (primo avvio guidato, inviti, recupero password) e il WP11 cala di uno (installazione PWA rimandata alla 2.0): il totale non cambia. La predisposizione alla traduzione pesa in tutto per circa 4-6 giorni-persona, cioè 2-3 settimane: circa 1 giorno-persona nel WP0 (impostazione di react-i18next, Babel e modelli mail per lingua, primi controlli nella pipeline: attività M0-06), 2-3 nel WP14 in M6 (estrazione delle stringhe residue e controlli automatici completi) e circa 1-2 distribuiti nei pacchetti dei singoli moduli, dove l'uso delle chiavi di traduzione è già compreso nella stima. Se le ore effettive di sviluppo sono meno di 16 (riunioni, imprevisti, cambi di contesto), le durate si allungano in proporzione: a 12 ore effettive, circa un terzo in più. Il piano va ricalibrato a fine M1 con i tempi reali.

La preparazione alla pubblicazione open source (paragrafo 11.14) non è inclusa in queste stime e va pianificata con la 3.0.

### 11.8 Priorità (MoSCoW) per la 1.0

| Priorità | Funzionalità |
| --- | --- |
| Must | Autenticazione, case/veicoli, visibilità, scadenze, pagamenti e quote, mail, backup |
| Should | Manutenzioni e catalogo, contatori, spesa, faccende, calendario |
| Could | Note, ricerca globale, log attività, esportazione ICS |
| Won't (ora) | Accesso esterno, push, report economici, estrazione automatica da PDF |

Le funzionalità Could fanno parte dell'ambito e del piano della 1.0 (paragrafo 11.2), ma sono un obiettivo non vincolante: se a fine M5 non sono pronte, il rilascio procede senza di esse e le funzionalità mancanti slittano a una versione 1.x.

### 11.9 Registro dei rischi

| Rischio | Probabilità | Impatto | Mitigazione |
| --- | --- | --- | --- |
| Gmail cambia regole o limita l'invio (per esempio dismissione delle password per le app, già avvenuta per Google Workspace) | Media | Alto | Livello di invio astratto: si passa a un servizio transazionale (Brevo, SMTP2GO) cambiando solo la configurazione; valutazione già fatta in M0 |
| Errori su ricorrenze e ora legale | Media | Alto | Test su date limite, fuso `Europe/Rome` esplicito |
| Dato privato esposto per una query dimenticata | Bassa | Alto | Filtro unico nel backend e test automatici di visibilità su ogni endpoint |
| Quote sbagliate per arrotondamenti | Media | Medio | Importi in centesimi, test sui valori limite, resto sull'ultima quota |
| Perdita dati (disco, errore, migrazione) | Bassa | Alto | Backup giornaliero cifrato su supporto separato, ripristino provato, backup prima di ogni migrazione |
| Server domestico come punto unico di guasto | Media | Medio | Riavvio automatico, backup su supporto separato, procedura di ripristino scritta |
| Ampliamento continuo dell'ambito | Alta | Medio | Backlog con priorità, richieste di modifica registrate, versioni 2.0 e 3.0 separate |
| Poco tempo disponibile | Media | Medio | Rilascio incrementale: il valore arriva già a M2 |
| Traffico in chiaro sulla rete locale (HTTP nella 1.0) | Bassa | Medio | Rete Wi-Fi cifrata con password robusta, nessun accesso dall'esterno, HTTPS già predisposto per la 2.0 |
| Primo avvio intercettato da un altro dispositivo in rete | Bassa | Alto | Codice monouso nei log del server, schermata disattivata dopo il primo utente |
| Mail finite nello spam | Media | Medio | Mittente dedicato e coerente, oggetti chiari, controllo periodico |
| Dati sugli stipendi esposti | Bassa | Alto | Accesso limitato al proprietario, nessuno stipendio nei log o nelle mail |
| Segreti o dati personali finiti nel repository, poi reso pubblico | Media | Alto | Configurazione fuori dal controllo di versione, analisi dei segreti dal primo commit, dati di prova solo fittizi (paragrafo 11.14) |
| Backup solo locale: incendio, furto o allagamento distruggono server e copia | Bassa | Alto | Destinazione configurabile: supporto in una stanza diversa dal server, due supporti a rotazione, oppure seconda destinazione fuori casa (SFTP o S3) senza modifiche al codice |

### 11.10 Strategia di qualità e test

- **Test unitari:** ricorrenze, calcolo delle quote, calcolo delle prossime scadenze di manutenzione.
- **Test di integrazione:** API con database reale in container.
- **Test di visibilità:** per ogni endpoint, verifica che l'altro utente non veda gli elementi privati.
- **Test su casi limite:** quote con importi dispari, cambio di ora legale, fine mese, anni bisestili.
- **Test end-to-end:** flussi principali con Playwright.
- **Analisi statica:** ruff, mypy, ESLint e formattazione, bloccanti nella pipeline.
- **Definizione di completato:** codice rivisto, test passanti, migrazione verificata, interfaccia provata da smartphone, documentazione aggiornata.

### 11.11 Ambienti, rilascio e operatività

- **Ambienti:** sviluppo locale con Docker Compose; produzione sul server domestico. Un ambiente di prova opzionale sullo stesso server con dati fittizi.
- **Repository:** monorepo (backend, frontend, infrastruttura) su GitHub; integrazione continua con GitHub Actions; versionamento semantico; rami brevi con revisione del codice.
- **Backup:** giornaliero e cifrato (restic), con la chiave conservata separatamente dai backup. **La destinazione la sceglie l'amministratore di sistema** nella configurazione del server (file di configurazione e variabili d'ambiente), senza modifiche al codice: percorso locale (disco esterno o altro supporto montato, predefinito), condivisione di rete montata (SMB/NFS), SFTP oppure archivio compatibile S3. Lo stesso meccanismo permette in futuro una seconda copia fuori casa. GitHub non è usato per i dati, perché contengono informazioni personali (stipendi, note private, allegati) e non è pensato per archiviare backup. Limite da conoscere: con la sola destinazione locale predefinita, incendio, furto o allagamento possono distruggere server e copia (registro dei rischi).
- **Rilascio:** immagini Docker versionate; migrazioni Alembic eseguite dopo un backup automatico; procedura di ritorno alla versione precedente documentata.
- **Monitoraggio:** controllo dello stato dei servizi, log strutturati, avviso via mail se falliscono invio mail o backup.
- **Manutenzione continua:** aggiornamento periodico delle dipendenze con strumenti automatici; prova di ripristino da backup ogni trimestre.

### 11.12 Governo del progetto

- **Backlog unico** con priorità MoSCoW, revisionato a ogni milestone.
- **Registro delle decisioni:** ogni scelta architetturale rilevante in una breve nota datata (cosa, perché, alternative scartate). Questo documento ne è la base.
- **Gestione delle modifiche:** ogni richiesta fuori ambito viene registrata, stimata e assegnata a una milestone o a una versione successiva.
- **Revisione a fine milestone:** cosa è stato consegnato, impegno reale rispetto alla stima, rischi nuovi.
- **Registrazione delle ore effettive:** ogni attività è una issue di GitHub collegata al pacchetto di lavoro (etichetta `WPn`) e alla milestone. Su un GitHub Project si usano due campi numerici, "Stima (ore)" e "Ore effettive", aggiornati alla chiusura della issue; un giorno-persona vale 8 ore. A fine milestone si confrontano i totali per pacchetto di lavoro. A fine M1 il rapporto ore effettive / ore stimate diventa il fattore di correzione delle milestone successive, applicato anche alla stima dell'effetto dello sviluppo assistito (paragrafo 11.6).

### 11.13 Criteri di accettazione della 1.0

1. Tutti i moduli della Must e della Should funzionano da computer e da smartphone sulla rete locale. Le funzionalità Could non sono vincolanti per il rilascio (paragrafo 11.8): quelle incluse devono rispettare gli stessi criteri, quelle mancanti passano a una 1.x.
2. Le mail arrivano secondo le cadenze, senza doppi invii, e restano nelle caselle ordinarie.
3. Nessun elemento privato è visibile all'altro utente, in nessuna schermata né mail (eccetto il segnaposto "Occupato" degli eventi).
4. Le quote dei pagamenti sono corrette e la loro somma coincide sempre con l'importo reale.
5. Il catalogo di manutenzione si può modificare dall'interfaccia senza intervenire sul database.
6. Il ripristino da backup è stato provato e documentato.
7. Aurora ha usato l'app per almeno due settimane e ha approvato i flussi principali.
8. Nessun testo visibile all'utente è scritto direttamente nel codice: tutto passa dai file di traduzione, con controllo automatico nella pipeline.

### 11.14 Predisposizione alla distribuzione open source (dopo la 3.0)

Poiché il codice verrà pubblicato, conviene lavorare fin dall'inizio come se fosse già pubblico.

- **Nessun segreto o dato personale nel repository:** configurazione in un file `.env` escluso dal controllo di versione, con un `.env.example` e i Docker secrets.
- **Analisi dei segreti dal primo commit:** funzione di scansione di GitHub e uno strumento locale prima di ogni commit (per esempio gitleaks). La cronologia di Git diventa pubblica insieme al codice: un segreto inserito e poi cancellato resta recuperabile.
- **Dati di prova solo fittizi** in test, esempi e schermate.
- **Catalogo di manutenzione iniziale** generico, con i riferimenti italiani (revisione, bollo, ecc.) separati come "profilo Italia", così un futuro contributore potrà aggiungere altri paesi.
- **Licenza: AGPL-3.0-or-later** (scelta delegata). Motivi: è un'applicazione web pensata per l'auto-ospitalità e questa è la licenza di progetti simili (per esempio Mealie, Vikunja, Firefly III); obbliga chi offre una versione modificata come servizio in rete a pubblicarne il codice, quindi impedisce che venga chiusa in un servizio commerciale, mentre per chi la installa a casa propria non cambia nulla. Alternative scartate: MIT e Apache-2.0 (adozione più facile ma nessuna protezione dal riuso chiuso) e GPL-3.0 (non copre l'uso come servizio in rete). Azioni: file `LICENSE` e intestazioni SPDX fin dal primo commit; verifica di compatibilità con le dipendenze (in particolare quelle GPL-2.0-only, incompatibili); prima di accettare contributi esterni, scegliere tra DCO (semplice, ma poi cambiare licenza richiede il consenso dei contributori) e CLA (permette di cambiare licenza). Non sono un avvocato: se il progetto avrà un uso commerciale, conviene una verifica legale prima della pubblicazione.
- **Traduzione:** predisposta fin dalla 1.0 (scelte tecniche nel paragrafo 11.15); nella 1.0 si distribuisce solo l'italiano.
- **Documentazione pubblica:** README, guida di installazione con Docker Compose, guida ai contributi, codice di condotta, modelli per segnalare problemi.
- **Stima:** la preparazione alla pubblicazione (pulizia, documentazione, licenza, verifica della cronologia) non è nel totale della 1.0 e va stimata nel piano della 3.0.

### 11.15 Predisposizione alla traduzione: scelte tecniche

| Area | Scelta |
| --- | --- |
| Frontend | react-i18next con un file JSON per lingua; chiavi stabili (non il testo come chiave); formato ICU per plurali e variabili; date, numeri e importi con `Intl` |
| Backend | errori e validazioni restituiti come codici stabili (per esempio `payment.shares_mismatch`) e tradotti dal frontend; nessun testo per l'utente nel codice |
| Mail | modelli Jinja2 per lingua (oggetto e corpo), testi con Babel/gettext; la lingua è quella del destinatario |
| Dati iniziali | le tipologie di manutenzione predefinite hanno una chiave di traduzione e le traduzioni nei file di lingua; quelle create dall'utente restano nel testo scritto da lui |
| Utente | campo `lingua` (predefinito `it`); fuso `Europe/Rome` e valuta euro restano fissi nella 1.0 |
| Controlli | nella pipeline: chiavi mancanti o inutilizzate, divieto di stringhe visibili scritte nel codice (regola di analisi statica), lingua di riferimento `it` |
| Fuori ambito | altre lingue (solo l'infrastruttura), scrittura da destra a sinistra, valute diverse dall'euro |

### 11.16 Prerequisiti di avvio

Da completare prima o durante la prima settimana di M0 (attività M0-01 del paragrafo 11.17).

**Server domestico**

| Requisito | Valore |
| --- | --- |
| Sistema operativo | Ubuntu Server LTS (24.04 o 26.04), architettura x86-64 o ARM64 |
| Risorse minime | 2 core, 4 GB di RAM (8 consigliati), 20 GB liberi per l'app più lo spazio per gli allegati |
| Software | Docker Engine aggiornato con Docker Compose v2 |
| Rete | Indirizzo IP riservato sul router e nome fisso in rete locale (`zeus.fritz.box`) |
| Orologio | Sincronizzazione NTP attiva (indispensabile per mail e scadenze) |
| Backup | Supporto di destinazione disponibile e montato (predefinito: disco locale separato da quello del sistema) |

**Versioni di riferimento** (fissate nel repository e aggiornate con Dependabot o Renovate)

| Componente | Versione | Nota |
| --- | --- | --- |
| Python | 3.14 | La 3.15 esce in autunno 2026: passaggio da valutare dopo M1, quando le librerie usate la supportano |
| Node.js (solo per la compilazione del frontend) | 24 LTS | Passaggio alla 26 quando diventa LTS |
| PostgreSQL | 18 | Aggiornamento di versione maggiore pianificato, sempre dopo un backup |
| Caddy | 2.x | Reverse proxy, HTTP in rete locale nella 1.0 |
| Gestione dipendenze | uv (Python), npm (frontend) | File di blocco delle versioni inclusi nel repository |

Le versioni esatte vanno ricontrollate all'avvio di M0 e registrate nella prima nota del registro delle decisioni.

**Account e servizi**

| Elemento | Responsabile | Stato |
| --- | --- | --- |
| Account Gmail dedicato con verifica in due passaggi e password per le app | Camillo | da fare |
| Repository GitHub (privato fino alla pubblicazione open source) con analisi dei segreti attiva | Camillo | da fare |
| GitHub Project con i campi "Stima (ore)" e "Ore effettive" | Camillo | da fare |
| Disponibilità di Aurora per il collaudo dopo M2 e in M6 | Aurora | da confermare |

**Postazione di sviluppo**

Git, Docker (su Windows: Docker Desktop con WSL2, lavorando dentro il file system di WSL per avere prestazioni adeguate), uv, Node.js, editor con supporto per Python e TypeScript, eventuali strumenti di sviluppo assistito.

### 11.17 Backlog della milestone M0

Ogni attività diventa una issue con etichetta `WP0`. Totale stimato: circa 46 ore, cioè 5,75 giorni-persona, dentro la stima di 4-6 del WP0.

| ID | Attività | Stima (ore) | Criterio di completamento |
| --- | --- | --- | --- |
| M0-01 | Verifica dei prerequisiti (paragrafo 11.16) | 2 | Tutte le voci della checklist risultano fatte o con una data |
| M0-02 | Repository: struttura del monorepo (`backend/`, `frontend/`, `infra/`, `docs/`), `LICENSE` AGPL, intestazioni SPDX, `.gitignore`, `.env.example`, README minimo, gitleaks prima di ogni commit | 3 | Primo commit senza segreti; gitleaks blocca un segreto di prova |
| M0-03 | Scheletro del backend: FastAPI, configurazione da variabili d'ambiente, endpoint `/health`, ruff e mypy | 5 | `/health` risponde; ruff e mypy senza errori |
| M0-04 | Database: PostgreSQL in Compose, SQLAlchemy, prima migrazione Alembic, test di integrazione con il database in container | 5 | La migrazione crea e annulla lo schema; il test di integrazione passa in locale e nella pipeline |
| M0-05 | Scheletro del frontend: Vite, React, TypeScript, TanStack Query, router, layout responsive di base, ESLint e Prettier | 5 | La pagina mostra lo stato di `/health`, da computer e da smartphone |
| M0-06 | Infrastruttura di traduzione: react-i18next con `it.json`, Babel nel backend, un modello mail Jinja2 di prova, controllo delle chiavi mancanti e della regola contro i testi scritti nel codice | 8 | Una stringa scritta direttamente nel codice fa fallire la pipeline |
| M0-07 | Docker Compose: backend, frontend compilato servito da Caddy, PostgreSQL, volumi per database e allegati, Docker secrets, configurazioni di sviluppo e produzione | 5 | `docker compose up` avvia tutto da zero su una macchina pulita |
| M0-08 | Pipeline GitHub Actions: analisi statica, controllo dei tipi, test di backend e frontend, compilazione delle immagini, gitleaks, controllo delle traduzioni | 4 | Pipeline verde sul ramo principale e bloccante sulle pull request |
| M0-09 | Primo deploy sul server domestico con il nome in rete locale | 3 | L'app risponde su `http://zeus.fritz.box` da computer e smartphone |
| M0-10 | Mail di prova tramite Gmail dal server, attraverso il livello di invio astratto | 2 | La mail arriva nella posta in arrivo e non nello spam |
| M0-11 | Impostazione del GitHub Project e creazione delle issue di M1 con stima | 2 | Tutte le attività di M1 sono nel Project, con stima in ore |
| M0-12 | Registro delle decisioni in `docs/adr/`: prime note (stack, licenza, HTTP in rete locale, allegati su volume) | 2 | Note presenti nel repository |

Il backup con restic resta nel WP12, ma il volume degli allegati e quello del database sono già separati e montabili dal backup.

**Criterio di uscita da M0:** pipeline verde, app raggiungibile in rete locale, mail di prova ricevuta, backlog di M1 stimato, ore effettive di M0 registrate.

---

## Appendice A: catalogo delle tipologie di manutenzione

**Come si usa.** Il catalogo è un insieme di dati iniziali caricati con le migrazioni (tabella `TipoManutenzione`). Il catalogo è **modulare**: voci, intervalli e promemoria si possono aggiungere, modificare e rimuovere dall'interfaccia, e adattare per singola casa o veicolo (regole nel paragrafo A.7).

**Classi.**

- **Ordinaria:** programmata, ricorrente a intervallo di tempo e/o chilometri. Genera scadenze e promemoria.
- **Straordinaria:** a evento (guasto, danno, lavoro una tantum). Non ha intervallo: si registra come intervento, con motivo, preventivo, importo finale, fornitore, garanzia e flag di detraibilità (utile nella 3.0).

**Avvertenza.** Gli intervalli indicati sono valori tipici di partenza. Quelli di legge (revisione, bollo, controlli degli impianti) variano per regione, potenza dell'impianto o data di immatricolazione e vanno verificati. Per i componenti prevale sempre il libretto di uso e manutenzione del costruttore.

### A.1 Casa: manutenzione ordinaria

| Area | Tipologia | Intervallo tipico |
| --- | --- | --- |
| Riscaldamento | Manutenzione caldaia (controllo e pulizia) | annuale, o secondo libretto |
| Riscaldamento | Controllo di efficienza energetica / rapporto di efficienza | 2-4 anni, secondo potenza e regione |
| Riscaldamento | Pulizia canna fumaria / camino / stufa a legna | annuale, prima dell'inverno |
| Riscaldamento | Manutenzione stufa o caldaia a pellet | annuale, con pulizia periodica |
| Riscaldamento | Spurgo termosifoni e controllo pressione impianto | annuale, in autunno |
| Riscaldamento | Manutenzione pompa di calore | annuale |
| Climatizzazione | Pulizia filtri condizionatore | ogni 1-3 mesi di uso |
| Climatizzazione | Sanificazione e controllo condizionatore | annuale, in primavera |
| Acqua | Controllo anodo e decalcificazione scaldabagno/boiler | ogni 2 anni circa |
| Acqua | Rifornimento sale e controllo addolcitore | mensile |
| Acqua | Cambio cartucce filtri acqua / depuratore | ogni 6 mesi circa |
| Acqua | Controllo autoclave e cisterna | annuale |
| Acqua | Pulizia sifoni, pozzetti e scarichi | annuale |
| Acqua | Svuotamento fossa settica / Imhoff | annuale, o secondo regolamento locale |
| Impianto elettrico | Test del salvavita (pulsante di prova) | mensile |
| Impianto elettrico | Verifica generale dell'impianto elettrico e della messa a terra | consigliata ogni 5 anni |
| Sicurezza | Test rilevatori di fumo e sostituzione batterie | test mensile, batterie annuali |
| Sicurezza | Sostituzione rilevatori di fumo e di gas a fine vita | 5-10 anni, secondo il modello |
| Sicurezza | Controllo e revisione estintore | controllo semestrale, revisione ogni 5 anni |
| Energia | Pulizia e controllo impianto fotovoltaico e inverter | annuale |
| Struttura | Ispezione tetto e coperture | annuale, e dopo eventi atmosferici forti |
| Struttura | Pulizia grondaie e pluviali | 1-2 volte l'anno, in autunno |
| Struttura | Controllo impermeabilizzazione terrazzi e balconi | annuale |
| Struttura | Lubrificazione e controllo infissi, tapparelle, serrature | annuale |
| Struttura | Controllo e sostituzione guarnizioni e silicone (bagno, cucina) | annuale |
| Finiture | Tinteggiatura pareti | 5-10 anni |
| Finiture | Trattamento parquet (lucidatura/oliatura) | 3-5 anni |
| Elettrodomestici | Pulizia filtro lavatrice e lavastoviglie | mensile |
| Elettrodomestici | Decalcificazione lavatrice e lavastoviglie | ogni 3 mesi circa |
| Elettrodomestici | Pulizia e sbrinamento frigorifero e congelatore | semestrale |
| Elettrodomestici | Pulizia e sostituzione filtri cappa (grassi / carbone) | 1-2 mesi (grassi), 3-6 mesi (carbone) |
| Elettrodomestici | Pulizia forno e piano cottura | trimestrale |
| Giardino | Potatura piante e siepi | stagionale |
| Giardino | Svernamento impianto di irrigazione (autunno) e riattivazione (primavera) | annuale |
| Giardino | Manutenzione tosaerba e attrezzi (affilatura, olio, candela) | annuale |
| Igiene | Disinfestazione (insetti, roditori) | annuale, o a evento |

### A.2 Casa: scadenze amministrative collegate

| Tipologia | Intervallo tipico |
| --- | --- |
| Polizza assicurativa della casa | annuale |
| Attestato di prestazione energetica (APE) | validità di 10 anni |
| Certificazioni e libretti degli impianti | secondo l'impianto |
| Garanzie di elettrodomestici e lavori | a data di scadenza |

Questi elementi generano una `Scadenza` con il relativo pagamento, e non solo una manutenzione.

### A.3 Casa: manutenzione straordinaria

Senza intervallo; si registra come intervento a evento.

| Area | Tipologia |
| --- | --- |
| Impianti | Sostituzione caldaia o installazione pompa di calore |
| Impianti | Riparazione guasto caldaia / scaldabagno |
| Impianti | Rifacimento impianto elettrico |
| Impianti | Rifacimento impianto idraulico o termico |
| Impianti | Installazione nuovi impianti (fotovoltaico, climatizzazione, domotica, allarme) |
| Struttura | Rifacimento tetto o coperture |
| Struttura | Rifacimento impermeabilizzazione di terrazzi e balconi |
| Struttura | Sostituzione infissi |
| Struttura | Ripristino facciata / lavori condominiali |
| Struttura | Riparazione di perdite e infiltrazioni |
| Struttura | Bonifica (muffa, umidità di risalita, amianto) |
| Ristrutturazione | Rifacimento bagno o cucina |
| Ristrutturazione | Ristrutturazione di locali (pavimenti, intonaci, tramezzi) |
| Sicurezza | Sostituzione porta blindata o serrature |
| Emergenze | Interventi urgenti (idraulico, fabbro, elettricista) |
| Emergenze | Ripristino dopo evento (allagamento, incendio, grandine, furto) |
| Elettrodomestici | Riparazione o sostituzione di un elettrodomestico guasto |
| Esterni | Abbattimento o messa in sicurezza di alberi, rifacimento recinzioni e muri |

### A.4 Auto: manutenzione ordinaria

| Area | Tipologia | Intervallo tipico |
| --- | --- | --- |
| Tagliando | Tagliando completo | 15.000-30.000 km o 12-24 mesi, secondo libretto |
| Motore | Cambio olio e filtro olio | 15.000 km o 12 mesi (spesso nel tagliando) |
| Motore | Sostituzione filtro aria | 30.000 km circa |
| Motore | Sostituzione filtro carburante | 30.000-60.000 km |
| Motore | Sostituzione candele (benzina) | 30.000-60.000 km |
| Motore | Cinghia di distribuzione (catena: solo controllo) | secondo libretto (km e anni) |
| Fluidi | Sostituzione liquido freni | ogni 2 anni |
| Fluidi | Sostituzione liquido di raffreddamento | secondo libretto |
| Fluidi | Controllo antigelo e livelli | annuale, in autunno |
| Freni | Controllo e sostituzione pastiglie | controllo a ogni tagliando, sostituzione a usura |
| Freni | Controllo e sostituzione dischi | controllo a ogni tagliando, sostituzione a usura |
| Pneumatici | Cambio stagionale (estivi/invernali) | 2 volte l'anno; dotazione invernale dove prevista, di norma dal 15 novembre al 15 aprile |
| Pneumatici | Controllo pressione | mensile |
| Pneumatici | Equilibratura, convergenza, rotazione | 10.000-20.000 km o annuale |
| Pneumatici | Sostituzione a usura (battistrada minimo 1,6 mm) | a usura |
| Elettrico | Controllo batteria | annuale; sostituzione tipica a 4-6 anni |
| Comfort | Sostituzione filtro abitacolo | 15.000 km o 12 mesi |
| Comfort | Sanificazione e controllo climatizzatore | ogni 2 anni |
| Visibilità | Sostituzione tergicristalli | annuale |
| Visibilità | Controllo luci e lampade | semestrale |
| Dotazione | Controllo kit di emergenza e kit gonfiaggio (liquido a scadenza) | annuale |
| Impianti a gas | Collaudo/revisione bombole metano | ogni 4 anni |
| Impianti a gas | Revisione serbatoio GPL | ogni 10 anni |

### A.5 Auto: scadenze amministrative

| Tipologia | Intervallo tipico |
| --- | --- |
| Revisione ministeriale | la prima a 4 anni dall'immatricolazione, poi ogni 2 anni |
| Bollo auto | annuale, con mese di scadenza variabile per veicolo |
| Assicurazione RCA | annuale (o semestrale) |
| Altre coperture (furto/incendio, kasko, assistenza stradale) | annuale |
| Garanzia / estensione di garanzia | a data di scadenza |

### A.6 Auto: manutenzione straordinaria

| Area | Tipologia |
| --- | --- |
| Motore e trasmissione | Riparazione motore, cambio o differenziale |
| Motore e trasmissione | Sostituzione frizione e volano |
| Motore e trasmissione | Sostituzione turbina |
| Scarico | Sostituzione o pulizia FAP/DPF, catalizzatore, sonda lambda |
| Telaio | Sostituzione ammortizzatori, molle, boccole, braccetti |
| Freni | Riparazione impianto frenante (pinze, pompa, tubazioni) |
| Elettrico | Riparazione centralina, alternatore, motorino di avviamento |
| Elettrico | Sostituzione batteria per guasto prematuro |
| Comfort | Riparazione climatizzatore (compressore, perdite) |
| Carrozzeria | Carrozzeria, verniciatura e riparazione sinistri (con collegamento alla pratica assicurativa) |
| Carrozzeria | Danni da grandine, furto o atti vandalici |
| Vetri | Sostituzione parabrezza o cristalli |
| Impianti | Installazione impianto GPL/metano |
| Richiami | Interventi per richiamo della casa costruttrice |

Mappatura con le funzioni dell'app: le voci ordinarie con intervallo generano scadenze nel calendario e mail secondo il paragrafo 5; le voci amministrative creano anche una `Scadenza` con pagamento e quote (paragrafo 7); le voci straordinarie alimentano lo storico costi per casa e veicolo.

### A.7 Gestione del catalogo (modularità)

Il catalogo si gestisce da una schermata di impostazioni, senza intervenire sul database.

| Azione | Comportamento |
| --- | --- |
| **Aggiungere** | Nuova tipologia con nome, ambito, classe, categoria, intervallo e promemoria; origine "personalizzato" |
| **Modificare** | Ogni campo è modificabile; le manutenzioni già create mantengono il proprio intervallo se è stato personalizzato, altrimenti seguono il nuovo valore predefinito |
| **Disattivare** | La tipologia non è più proponibile per nuove manutenzioni; quelle esistenti e lo storico restano intatti |
| **Rimuovere** | Eliminazione definitiva consentita solo se la tipologia non è mai stata usata; altrimenti viene archiviata, per non perdere lo storico degli interventi |
| **Adattare per casa o veicolo** | Intervallo e promemoria si sovrascrivono sulla singola manutenzione, senza toccare il catalogo |
| **Ripristinare** | Una voce predefinita modificata si può riportare al valore originale |
| **Esportare e importare** | Catalogo in formato JSON, per copiarlo o ripristinarlo |

Aggiornamenti del catalogo iniziale: le migrazioni aggiungono le nuove voci predefinite, ma non sovrascrivono mai quelle modificate o disattivate dall'utente (campi `origine` e `modificato dall'utente`).
