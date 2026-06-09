import js from '@eslint/js';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import prettierConfig from 'eslint-config-prettier';
import perfectionist from 'eslint-plugin-perfectionist';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import unusedImports from 'eslint-plugin-unused-imports';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: globals.browser,
    },
    plugins: {
      '@typescript-eslint': tseslint,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      perfectionist,
      'unused-imports': unusedImports,
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'no-unused-vars': 'off',
      // TypeScript reports undefined identifiers itself (incl. DOM lib types);
      // with no-undef active every DOM global would need hand-listing here.
      'no-undef': 'off',
      // Allow ref updates during render (common pattern for keeping refs in sync)
      'react-hooks/refs': 'off',
      'unused-imports/no-unused-imports': 'error',
      'perfectionist/sort-imports': [
        'error',
        {
          type: 'natural',
          newlinesBetween: 1,
          internalPattern: ['^src/'],
          groups: [
            'side-effect-style',
            'side-effect',
            'react',
            ['builtin', 'external'],
            'mui',
            'internal',
            ['parent', 'sibling', 'index'],
            'unknown',
          ],
          customGroups: [
            { groupName: 'react', elementNamePattern: ['^react$', '^react-dom'] },
            { groupName: 'mui', elementNamePattern: ['^@mui/'] },
          ],
        },
      ],
      'perfectionist/sort-named-imports': ['error', { type: 'natural' }],
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**', 'coverage/**', '*.config.js', '*.config.mjs'],
  },
  prettierConfig,
];
