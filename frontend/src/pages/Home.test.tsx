// SPDX-License-Identifier: AGPL-3.0-or-later
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

import { Home } from './Home';

function renderizza() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <Home />
    </QueryClientProvider>,
  );
}

function rispondi(status: number, corpo: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(new Response(JSON.stringify(corpo), { status })),
  );
}

afterEach(() => vi.unstubAllGlobals());

test('mostra lo stato ok con la versione', async () => {
  rispondi(200, { status: 'ok', database: 'ok', version: '0.1.0' });
  renderizza();
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Benvenuti');
  expect(await screen.findByText('Tutto funziona (versione 0.1.0)')).toBeInTheDocument();
});

test('segnala il database non raggiungibile', async () => {
  rispondi(503, { status: 'error', database: 'error', version: '0.1.0' });
  renderizza();
  expect(await screen.findByText('Il database non risponde')).toBeInTheDocument();
});

test('segnala il server non raggiungibile', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('rete')));
  renderizza();
  expect(await screen.findByText('Il server non è raggiungibile')).toBeInTheDocument();
});
