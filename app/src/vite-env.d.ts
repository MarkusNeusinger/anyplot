/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Deep ESM imports not covered by @types/react-syntax-highlighter
declare module 'react-syntax-highlighter/dist/esm/prism-light';
declare module 'react-syntax-highlighter/dist/esm/styles/prism';
declare module 'react-syntax-highlighter/dist/esm/languages/prism/python';
