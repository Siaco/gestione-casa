// SPDX-License-Identifier: AGPL-3.0-or-later
// Client HTTP: il backend restituisce errori come codici stabili, tradotti qui nel frontend.

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly params: Record<string, unknown> = {},
  ) {
    super(code);
    this.name = 'ApiError';
  }

  /** Chiave di traduzione dell'errore (es. `errori.payment.shares_mismatch`). */
  get chiaveTraduzione(): string {
    return `errori.${this.code}`;
  }
}

// Token CSRF della sessione (M1-04): ricevuto da login e /api/auth/me, tenuto solo in memoria
let tokenCsrf: string | null = null;

export function impostaTokenCsrf(token: string | null): void {
  tokenCsrf = token;
}

interface CorpoErrore {
  error?: { code?: string; params?: Record<string, unknown> };
}

async function leggiRisposta<T>(risposta: Response): Promise<T> {
  const corpo: unknown = risposta.status === 204 ? null : await risposta.json().catch(() => null);
  if (!risposta.ok) {
    const errore = (corpo as CorpoErrore | null)?.error;
    throw new ApiError(risposta.status, errore?.code ?? 'sconosciuto', errore?.params ?? {});
  }
  return corpo as T;
}

export async function apiGet<T>(percorso: string): Promise<T> {
  const risposta = await fetch(`/api${percorso}`, {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  });
  return leggiRisposta<T>(risposta);
}

/** Richieste che modificano dati: corpo JSON e intestazione X-CSRF-Token. */
export async function apiSend<T>(
  metodo: 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  percorso: string,
  corpo?: unknown,
): Promise<T> {
  const intestazioni: Record<string, string> = { Accept: 'application/json' };
  if (corpo !== undefined) intestazioni['Content-Type'] = 'application/json';
  if (tokenCsrf) intestazioni['X-CSRF-Token'] = tokenCsrf;
  const risposta = await fetch(`/api${percorso}`, {
    method: metodo,
    credentials: 'same-origin',
    headers: intestazioni,
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  });
  return leggiRisposta<T>(risposta);
}
