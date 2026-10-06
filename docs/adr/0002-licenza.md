# 0002. Licenza AGPL-3.0-or-later

- Data: 2026-10-06
- Stato: approvata

## Contesto

Il progetto sarà pubblicato come open source al termine della 3.0. È un'applicazione web pensata per l'auto-ospitalità.

## Decisione

Licenza GNU AGPL-3.0-or-later, con file `LICENSE` e intestazioni SPDX in ogni file sorgente fin dal primo commit.

## Alternative scartate

MIT e Apache-2.0 (nessuna protezione dal riuso chiuso come servizio), GPL-3.0 (non copre l'uso come servizio in rete).

## Conseguenze

Va verificata la compatibilità delle dipendenze (in particolare quelle GPL-2.0-only). Prima di accettare contributi esterni bisogna scegliere tra DCO e CLA (documento iniziale, paragrafo 11.14). Il testo di `LICENSE` va confrontato con quello ufficiale su gnu.org prima della pubblicazione.
