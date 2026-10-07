#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Carica un backlog di milestone (docs/backlog/Mx.md) su GitHub:
# etichette WP0…WP14, milestone M0…M6, GitHub Project con i campi "Stima (ore)" e
# "Ore effettive", una issue per attività con la stima già compilata.
# Rieseguibile: ciò che esiste già non viene duplicato; le issue esistenti vengono aggiunte al Project
# (se mancano) e la loro stima viene riscritta.
#
# Requisiti: GitHub CLI (gh) autenticata con il permesso "project":
#   gh auth login            # se non l'hai mai fatto
#   gh auth refresh -s project
# Uso (dalla radice del repository; su Windows da Git Bash):
#   DRY_RUN=1 docs/backlog/carica-su-github.sh docs/backlog/M1.md   # mostra cosa farebbe
#   docs/backlog/carica-su-github.sh docs/backlog/M1.md
# Variabili facoltative: REPO (predefinito: il repository corrente), PROGETTO (titolo del Project).

set -euo pipefail

FILE="${1:-docs/backlog/M1.md}"
PROGETTO="${PROGETTO:-Gestione casa}"
DRY_RUN="${DRY_RUN:-0}"

[[ -f "$FILE" ]] || { echo "File non trovato: $FILE" >&2; exit 1; }

MILESTONE=$(sed -n 's/^- Milestone: *\(M[0-9]*\).*/\1/p' "$FILE" | tr -d "\r" | head -1)
WP=$(sed -n 's/^- Pacchetto di lavoro: *\(WP[0-9]*\).*/\1/p' "$FILE" | tr -d "\r" | head -1)
[[ -n "$MILESTONE" && -n "$WP" ]] || { echo "Intestazione senza 'Milestone' o 'Pacchetto di lavoro'" >&2; exit 1; }

# Una cartella temporanea con un file per attività: riga 1 = ID, riga 2 = titolo, riga 3 = ore, poi il corpo
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
awk -v dir="$TMP" '
  /^### / {
    n++; f = sprintf("%s/%03d", dir, n)
    intest = substr($0, 5); id = intest; titolo = intest
    sub(/ · .*/, "", id); sub(/^[^·]*· /, "", titolo)
    print id > f; print titolo > f; next
  }
  n && /^\*\*Stima:\*\*/ { match($0, /[0-9]+/); ore_val = substr($0, RSTART, RLENGTH); print ore_val > f }
  n { print > (f ".corpo") }
' "$FILE"

ATTIVITA=( "$TMP"/[0-9][0-9][0-9] )
[[ -e "${ATTIVITA[0]}" ]] || { echo "Nessuna attività trovata in $FILE" >&2; exit 1; }

echo "Milestone $MILESTONE, $WP, ${#ATTIVITA[@]} attività da $FILE"
TOTALE=0
for f in "${ATTIVITA[@]}"; do
  ID=$(sed -n 1p "$f"); TITOLO=$(sed -n 2p "$f"); ORE=$(sed -n 3p "$f")
  [[ "$ORE" =~ ^[0-9]+$ ]] || { echo "Stima mancante per $ID" >&2; exit 1; }
  TOTALE=$((TOTALE + ORE))
  printf '  [%s] %-60s %3s ore\n' "$ID" "$TITOLO" "$ORE"
done
echo "  Totale: $TOTALE ore"
[[ "$DRY_RUN" == "1" ]] && { echo "DRY_RUN=1: nessuna modifica su GitHub."; exit 0; }

command -v gh >/dev/null || { echo "Serve GitHub CLI (gh)." >&2; exit 1; }
REPO="${REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
OWNER="${REPO%%/*}"
echo "Repository: $REPO"

echo "Etichette WP0…WP14"
for i in $(seq 0 14); do
  gh label create "WP$i" --repo "$REPO" --color 1f6feb --description "Pacchetto di lavoro $i" --force >/dev/null
done

echo "Milestone M0…M6"
ESISTENTI=$(gh api "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')
for i in $(seq 0 6); do
  grep -qx "M$i" <<<"$ESISTENTI" || gh api -X POST "repos/$REPO/milestones" -f title="M$i" >/dev/null
done

echo "Project \"$PROGETTO\""
NUMERO=$(gh project list --owner "$OWNER" --format json --jq ".projects[] | select(.title == \"$PROGETTO\") | .number" | tr -d "\r" | head -1)
if [[ -z "$NUMERO" ]]; then
  NUMERO=$(gh project create --owner "$OWNER" --title "$PROGETTO" --format json --jq .number | tr -d "\r")
  gh project link "$NUMERO" --owner "$OWNER" --repo "$REPO" >/dev/null || true
fi
PROJECT_ID=$(gh project view "$NUMERO" --owner "$OWNER" --format json --jq .id | tr -d "\r")

campo() {  # campo <nome>: id del campo numerico, creato se manca
  local id
  id=$(gh project field-list "$NUMERO" --owner "$OWNER" --format json --jq ".fields[] | select(.name == \"$1\") | .id" | tr -d "\r")
  if [[ -z "$id" ]]; then
    id=$(gh project field-create "$NUMERO" --owner "$OWNER" --name "$1" --data-type NUMBER --format json --jq .id | tr -d "\r")
  fi
  echo "$id"
}
CAMPO_STIMA=$(campo "Stima (ore)")
campo "Ore effettive" >/dev/null

echo "Issue"
# titolo<TAB>url di tutte le issue (tr toglie eventuali \r di Windows)
ESISTENTI_ISSUE=$(gh issue list --repo "$REPO" --state all --limit 500 --json title,url --jq '.[] | "\(.title)\t\(.url)"' | tr -d '\r')
for f in "${ATTIVITA[@]}"; do
  ID=$(sed -n 1p "$f"); TITOLO=$(sed -n 2p "$f"); ORE=$(sed -n 3p "$f")
  NOME="[$ID] $TITOLO"
  URL=$(grep -F "[$ID] " <<<"$ESISTENTI_ISSUE" | head -1 | cut -f2 || true)
  if [[ -n "$URL" ]]; then
    STATO="esistente"
  else
    URL=$(gh issue create --repo "$REPO" --title "$NOME" --label "$WP" --milestone "$MILESTONE" --body-file "$f.corpo" | tr -d '\r')
    STATO="creata"
  fi
  # item-add è idempotente: se la issue è già nel Project restituisce l'elemento esistente
  ITEM=$(gh project item-add "$NUMERO" --owner "$OWNER" --url "$URL" --format json --jq .id | tr -d '\r')
  [[ -n "$ITEM" ]] || { echo "Impossibile aggiungere $URL al Project $NUMERO" >&2; exit 1; }
  gh project item-edit --id "$ITEM" --project-id "$PROJECT_ID" --field-id "$CAMPO_STIMA" --number "$ORE" >/dev/null
  echo "  $STATO: $NOME ($ORE ore) $URL"
done

echo "Fatto. Project: https://github.com/users/$OWNER/projects/$NUMERO"
