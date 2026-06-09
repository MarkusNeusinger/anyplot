import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import { checker } from 'vite-plugin-checker';
import { compression } from 'vite-plugin-compression2';

export default defineConfig({
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
    compression({ algorithm: 'gzip', threshold: 1024 }),
    compression({ algorithm: 'brotliCompress', threshold: 1024 }),
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
