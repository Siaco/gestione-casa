// SPDX-License-Identifier: AGPL-3.0-or-later
import { afterEach, vi } from 'vitest';

import { ApiError, apiSend, impostaTokenCsrf } from './client';

afterEach(() => {
  vi.unstubAllGlobals();
  impostaTokenCsrf(null);
});

test('le modifiche inviano il token CSRF e il corpo JSON', async () => {
  const fetchFinto = vi.fn().mockResolvedValue(new Response('{"ok":true}', { status: 200 }));
  vi.stubGlobal('fetch', fetchFinto);
  impostaTokenCsrf('abc123');

  await expect(apiSend('POST', '/case', { nome: 'Casa' })).resolves.toEqual({ ok: true });

  const [url, init] = fetchFinto.mock.calls[0] as [string, RequestInit];
  expect(url).toBe('/api/case');
  expect(init.method).toBe('POST');
  expect(init.headers).toMatchObject({
    'X-CSRF-Token': 'abc123',
    'Content-Type': 'application/json',
  });
  expect(init.body).toBe('{"nome":"Casa"}');
});

test('errore del backend con codice stabile', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        new Response('{"error":{"code":"auth.csrf_invalid","params":{}}}', { status: 403 }),
      ),
  );
  const errore = await apiSend('DELETE', '/case/1').catch((e: unknown) => e);
  expect(errore).toBeInstanceOf(ApiError);
  expect((errore as ApiError).chiaveTraduzione).toBe('errori.auth.csrf_invalid');
});

test('risposta 204 senza corpo', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
  await expect(apiSend('POST', '/auth/logout')).resolves.toBeNull();
});
