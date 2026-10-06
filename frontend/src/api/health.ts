// SPDX-License-Identifier: AGPL-3.0-or-later
import { useQuery } from '@tanstack/react-query';

import { ApiError } from './client';

export type Stato = 'ok' | 'error';

export interface Health {
  status: Stato;
  database: Stato;
  version: string;
}

/** Lo stato è utile anche quando il backend risponde 503 (database non raggiungibile). */
export async function leggiHealth(): Promise<Health> {
  const risposta = await fetch('/api/health', { headers: { Accept: 'application/json' } });
  if (risposta.status === 200 || risposta.status === 503) {
    return (await risposta.json()) as Health;
  }
  throw new ApiError(risposta.status, 'sconosciuto');
}

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: leggiHealth, refetchInterval: 60_000 });
}
