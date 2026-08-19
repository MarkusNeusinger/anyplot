/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_DEBUG_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Injected by vite.config.ts / vitest.config.ts from the [project] version in
// the repo-root pyproject.toml (see app/project-version.ts).
declare const __APP_VERSION__: string;

// Deep ESM imports not covered by @types/react-syntax-highlighter
declare module 'react-syntax-highlighter/dist/esm/prism-light';
declare module 'react-syntax-highlighter/dist/esm/styles/prism';
declare module 'react-syntax-highlighter/dist/esm/languages/prism/python';
