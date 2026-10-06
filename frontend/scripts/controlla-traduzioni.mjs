// SPDX-License-Identifier: AGPL-3.0-or-later
// Controllo delle traduzioni del frontend, eseguito nella pipeline:
// 1. ogni chiave usata nel codice esiste nella lingua di riferimento (it);
// 2. ogni chiave della lingua di riferimento è usata (salvo i prefissi dinamici);
// 3. ogni altra lingua ha esattamente le stesse chiavi della lingua di riferimento.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const RADICE = new URL('..', import.meta.url).pathname;
const SRC = join(RADICE, 'src');
const LOCALES = join(SRC, 'locales');
const RIFERIMENTO = 'it';
// Chiavi costruite a runtime (es. errori dal backend: `errori.${codice}`)
const PREFISSI_DINAMICI = ['errori.'];

const appiattisci = (oggetto, prefisso = '') =>
  Object.entries(oggetto).flatMap(([k, v]) =>
    v !== null && typeof v === 'object' ? appiattisci(v, `${prefisso}${k}.`) : [`${prefisso}${k}`],
  );

const file = (cartella) =>
  readdirSync(cartella).flatMap((nome) => {
    const percorso = join(cartella, nome);
    return statSync(percorso).isDirectory() ? file(percorso) : [percorso];
  });

const sorgenti = file(SRC).filter((f) => /\.(ts|tsx)$/.test(f) && !/\.test\.tsx?$/.test(f));
const usate = new Map();
const MODELLI = [/\bt\(\s*['"`]([\w.-]+)['"`]/g, /i18nKey=["']([\w.-]+)["']/g];
for (const f of sorgenti) {
  const testo = readFileSync(f, 'utf8');
  for (const re of MODELLI) {
    for (const m of testo.matchAll(re)) usate.set(m[1], relative(RADICE, f));
  }
}

const lingue = readdirSync(LOCALES)
  .filter((f) => f.endsWith('.json'))
  .map((f) => f.replace(/\.json$/, ''));
const chiavi = Object.fromEntries(
  lingue.map((l) => [
    l,
    new Set(appiattisci(JSON.parse(readFileSync(join(LOCALES, `${l}.json`), 'utf8')))),
  ]),
);
const riferimento = chiavi[RIFERIMENTO];
const errori = [];

for (const [k, f] of usate) {
  if (!riferimento.has(k))
    errori.push(`chiave mancante in ${RIFERIMENTO}.json: ${k} (usata in ${f})`);
}
for (const k of riferimento) {
  if (!usate.has(k) && !PREFISSI_DINAMICI.some((p) => k.startsWith(p))) {
    errori.push(`chiave non usata in ${RIFERIMENTO}.json: ${k}`);
  }
}
for (const l of lingue.filter((x) => x !== RIFERIMENTO)) {
  for (const k of riferimento) if (!chiavi[l].has(k)) errori.push(`${l}.json: manca ${k}`);
  for (const k of chiavi[l]) if (!riferimento.has(k)) errori.push(`${l}.json: chiave in più ${k}`);
}

if (errori.length) {
  for (const e of errori) console.error(`ERRORE: ${e}`);
  process.exit(1);
}
console.log(
  `Traduzioni del frontend: OK (${riferimento.size} chiavi, lingue: ${lingue.join(', ')})`,
);
