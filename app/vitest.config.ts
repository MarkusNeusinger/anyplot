import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: {
      src: fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    setupFiles: ['./src/setupTests.ts'],
    // MUI >= 9.1 ships .mjs files with directory imports (e.g.
    // react-transition-group/TransitionGroupContext) that Node's native ESM
    // loader rejects; inline MUI so Vite's resolver handles those imports.
    server: {
      deps: {
        inline: [/@mui\//],
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: [
        'src/utils/**/*.ts',
        'src/hooks/**/*.ts',
        'src/components/**/*.tsx',
        'src/pages/**/*.tsx',
        'src/constants/**/*.ts',
        'src/routes/**/*.ts',
        'src/theme/**/*.ts',
        'src/types/**/*.ts',
      ],
      exclude: ['src/**/*.test.ts', 'src/**/*.test.tsx', 'src/setupTests.ts', 'src/test-utils.tsx'],
    },
  },
});
