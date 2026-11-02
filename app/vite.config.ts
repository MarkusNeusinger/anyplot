import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import { checker } from 'vite-plugin-checker';
import { compression } from 'vite-plugin-compression2';

type ModuleLookup = (id: string) => { importers: readonly string[] } | null;

/**
 * The agent chat's full data view (`src/sections/agent-chat/DataView.tsx`) and
 * the MUI X Data Grid it renders load on demand. The `mui` chunk below loads
 * with every page, so a module only the view reaches, the grid itself or a MUI
 * component no other module imports, must not join it: it stays in the view's
 * lazy chunk. A module is the view's alone when it is a root (the grid's
 * packages, the view's own module) or when every module that imports it is.
 */
const DATA_VIEW_ROOTS = [/node_modules\/@mui\/x-/, /src\/sections\/agent-chat\/DataView\.tsx$/];
const dataViewOnly = new Map<string, boolean>();

function onlyTheDataView(id: string, lookup: ModuleLookup): boolean {
  const known = dataViewOnly.get(id);
  if (known !== undefined) return known;
  if (DATA_VIEW_ROOTS.some(root => root.test(id))) {
    dataViewOnly.set(id, true);
    return true;
  }
  // An import cycle reads as shared while it is being walked, so it never pulls a module out of `mui`.
  dataViewOnly.set(id, false);
  const importers = lookup(id)?.importers ?? [];
  const only =
    importers.length > 0 && importers.every(importer => onlyTheDataView(importer, lookup));
  dataViewOnly.set(id, only);
  return only;
}

export default defineConfig({
  resolve: {
    alias: {
      src: fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  plugins: [
    react(),
    // Dev-only TS + ESLint feedback in the browser overlay; the production
    // build already type-checks via `tsc && vite build`.
    checker({
      typescript: true,
      eslint: { lintCommand: 'eslint src', useFlatConfig: true },
      overlay: { initialIsOpen: false },
      enableBuild: false,
    }),
    // index.html is EXCLUDED, and that is load-bearing rather than tidiness.
    // nginx rewrites the shell per request to stamp the CSP nonce onto its
    // <script> tags (app/nginx.conf, app/security-headers.conf), and
    // `gzip_static on` would hand out the precompressed copy instead —
    // untouched, unstamped, and with a policy that then blocks every inline
    // script on the page. sub_filter only ever sees uncompressed bodies. The
    // hashed chunks under /assets/ are what precompression is actually for,
    // and they keep it; the shell is 11 kB and nginx still gzips it on the fly.
    compression({ algorithm: 'gzip', threshold: 1024, exclude: [/index\.html$/] }),
    compression({ algorithm: 'brotliCompress', threshold: 1024, exclude: [/index\.html$/] }),
  ],
  server: {
    port: 3000,
    host: true,
  },
  preview: {
    port: 3000,
    host: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id, { getModuleInfo }) {
          if (id.includes('node_modules/@mui/icons-material/')) return 'mui-icons';
          if (id.includes('node_modules/@mui/') && onlyTheDataView(id, getModuleInfo)) return null;
          if (id.includes('node_modules/@mui/')) return 'mui';
          if (id.includes('node_modules/@emotion/')) return 'mui';
          if (
            id.includes('node_modules/react/') ||
            id.includes('node_modules/react-dom/') ||
            id.includes('node_modules/react-router')
          )
            return 'vendor';
        },
      },
    },
  },
});
