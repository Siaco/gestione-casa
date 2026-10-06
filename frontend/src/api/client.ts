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

interface CorpoErrore {
  error?: { code?: string; params?: Record<string, unknown> };
}

export async function apiGet<T>(percorso: string, init?: RequestInit): Promise<T> {
  const risposta = await fetch(`/api${percorso}`, {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
    ...init,
  });
  const corpo: unknown = await risposta.json().catch(() => null);
  if (!risposta.ok) {
    const errore = (corpo as CorpoErrore | null)?.error;
    throw new ApiError(risposta.status, errore?.code ?? 'sconosciuto', errore?.params ?? {});
  }
  return corpo as T;
}
