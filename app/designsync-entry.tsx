/**
 * Curated entry point for the anyplot design system (/design-sync converter).
 *
 * Re-exports the reusable, presentational components plus an `AppProviders`
 * wrapper used to render the preview cards: the MUI theme, a CSS baseline, and
 * an in-memory router so the link-bearing components (SectionHeader, Footer)
 * render outside a real browser history.
 *
 * This file lives OUTSIDE the app tsconfig `include` (see
 * tsconfig.designsync.json) so the app's build and typecheck never touch it.
 * It exists only as the esbuild entry for the design-system bundle — importing
 * `src/main.tsx` (which calls ReactDOM.createRoot().render()) is deliberately
 * avoided so nothing mounts the real app when the bundle loads.
 */
import * as React from 'react';

import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from '@mui/material/styles';
import { MemoryRouter } from 'react-router-dom';

import { theme } from 'src/theme';

export { default as CodeHighlighter } from 'src/components/CodeHighlighter';
export { LoaderSpinner } from 'src/components/LoaderSpinner';
export { ThemeToggle } from 'src/components/ThemeToggle';
export { SectionHeader } from 'src/components/SectionHeader';
export { Footer } from 'src/layouts/Footer';

/**
 * Preview wrapper: applies the anyplot theme + CSS baseline and provides an
 * in-memory router so components that render react-router `Link`s work.
 */
export function AppProviders({ children }: { children?: React.ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </MemoryRouter>
  );
}
