import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import { checker } from 'vite-plugin-checker';
import { compression } from 'vite-plugin-compression2';

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
        manualChunks(id) {
          if (id.includes('node_modules/@mui/icons-material/')) return 'mui-icons';
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
