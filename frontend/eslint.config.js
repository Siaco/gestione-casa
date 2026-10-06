// SPDX-License-Identifier: AGPL-3.0-or-later
import js from '@eslint/js';
import i18next from 'eslint-plugin-i18next';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'coverage'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { ecmaVersion: 2023, globals: globals.browser },
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh, i18next },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // Nessun testo visibile scritto nel codice: tutto passa da i18next (paragrafo 11.15)
      'i18next/no-literal-string': ['error', { mode: 'jsx-only' }],
    },
  },
  {
    // Test e configurazione possono contenere testi letterali
    files: ['src/test/**', '**/*.test.{ts,tsx}', 'vite.config.ts'],
    rules: { 'i18next/no-literal-string': 'off' },
  },
  {
    files: ['scripts/**/*.mjs'],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
);
