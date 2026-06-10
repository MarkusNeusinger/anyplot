import { HelmetProvider } from 'react-helmet-async';
import { createBrowserRouter, Navigate, RouterProvider, useParams } from 'react-router-dom';

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';

import { ErrorBoundary } from 'src/components/ErrorBoundary';
import { RouteErrorBoundary } from 'src/components/RouteErrorBoundary';
import { AppDataProvider } from 'src/layouts/Layout';
import { RootLayout } from 'src/layouts/RootLayout';
import { NotFoundPage } from 'src/pages/NotFoundPage';

const LazyFallback = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
    <CircularProgress size={32} />
  </Box>
);

const lazySpec = () =>
  import('src/pages/SpecPage').then(m => ({
    Component: m.SpecPage,
    HydrateFallback: LazyFallback,
  }));

function SpecLanguageRedirect() {
  const { specId, language } = useParams();
  if (!specId || !language) return <NotFoundPage />;
  return (
    <Navigate
      to={{ pathname: `/${specId}`, search: `?language=${encodeURIComponent(language)}` }}
      replace
    />
  );
}

// A pathless child route with errorElement lets us keep the layout chrome
// (masthead/navbar/footer) when a child page fails to load. Errors in the
// layout itself still surface via the outer ErrorBoundary wrapping the router.
const router = createBrowserRouter([
  {
    element: <RootLayout />,
    // Surface a small spinner while a lazy() route is resolving during initial
    // hydration; without this React Router 6.4+ logs a noisy "No HydrateFallback
    // element provided" warning on every load.
    hydrateFallbackElement: <LazyFallback />,
    children: [
      {
        errorElement: <RouteErrorBoundary />,
        children: [
          {
            index: true,
            lazy: () => import('src/pages/LandingPage').then(m => ({ Component: m.LandingPage })),
          },
          {
            path: 'plots',
            lazy: () => import('src/pages/PlotsPage').then(m => ({ Component: m.PlotsPage })),
          },
          {
            path: 'specs',
            lazy: () =>
              import('src/pages/SpecsListPage').then(m => ({ Component: m.SpecsListPage })),
          },
          {
            path: 'libraries',
            lazy: () =>
              import('src/pages/LibrariesPage').then(m => ({ Component: m.LibrariesPage })),
          },
          {
            path: 'map',
            lazy: () => import('src/pages/MapPage').then(m => ({ Component: m.MapPage })),
          },
          {
            path: 'palette',
            lazy: () => import('src/pages/PalettePage').then(m => ({ Component: m.PalettePage })),
          },
          {
            path: 'about',
            lazy: () => import('src/pages/AboutPage').then(m => ({ Component: m.AboutPage })),
          },
          {
            path: 'legal',
            lazy: () => import('src/pages/LegalPage').then(m => ({ Component: m.LegalPage })),
          },
          {
            path: 'mcp',
            lazy: () => import('src/pages/McpPage').then(m => ({ Component: m.McpPage })),
          },
          {
            path: 'stats',
            lazy: () => import('src/pages/StatsPage').then(m => ({ Component: m.StatsPage })),
          },
          {
            path: 'debug',
            lazy: () => import('src/pages/DebugPage').then(m => ({ Component: m.DebugPage })),
          },
          { path: ':specId', lazy: lazySpec },
          { path: ':specId/:language', element: <SpecLanguageRedirect /> },
          { path: ':specId/:language/:library', lazy: lazySpec },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);

export function AppRouter() {
  return (
    <HelmetProvider>
      <ErrorBoundary>
        <AppDataProvider>
          <RouterProvider router={router} />
        </AppDataProvider>
      </ErrorBoundary>
    </HelmetProvider>
  );
}
