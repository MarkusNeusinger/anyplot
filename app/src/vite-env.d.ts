/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_DEBUG_API_URL?: string;
  /** `true` builds the admin-only agent chat page and the `.adapt()` button. */
  readonly VITE_ENABLE_AGENT_CHAT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Deep ESM imports not covered by @types/react-syntax-highlighter
declare module 'react-syntax-highlighter/dist/esm/prism-light';
declare module 'react-syntax-highlighter/dist/esm/styles/prism';
declare module 'react-syntax-highlighter/dist/esm/languages/prism/python';
