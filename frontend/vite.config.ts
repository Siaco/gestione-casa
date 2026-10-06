// SPDX-License-Identifier: AGPL-3.0-or-later
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// In sviluppo le chiamate /api vanno al backend locale (porta 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target: process.env.GC_BACKEND_URL ?? 'http://localhost:8000', ws: true },
    },
  },
  build: { sourcemap: true },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
});
