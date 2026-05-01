import { createBrowserRouter, Navigate, RouterProvider, useParams } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import { AppDataProvider } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { RootLayout } from './components/RootLayout';
import { RouteErrorBoundary } from './components/RouteErrorBoundary';
import { NotFoundPage } from './pages/NotFoundPage';

const LazyFallback = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
    <CircularProgress size={32} />
  </Box>
);

const lazySpec = () => import('./pages/SpecPage').then(m => ({ Component: m.SpecPage, HydrateFallback: LazyFallback }));

function SpecLanguageRedirect() {
  const { specId, language } = useParams();
  if (!specId || !language) return <NotFoundPage />;
  return <Navigate to={{ pathname: `/${specId}`, search: `?language=${encodeURIComponent(language)}` }} replace />;
}

// A pathless child route with errorElement lets us keep the layout chrome
// (masthead/navbar/footer) when a child page fails to load. Errors in the
// layout itself still surface via the outer ErrorBoundary wrapping the router.
const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      {
        errorElement: <RouteErrorBoundary />,
        children: [
          { index: true, lazy: () => import('./pages/LandingPage').then(m => ({ Component: m.LandingPage })) },
          { path: 'plots', lazy: () => import('./pages/PlotsPage').then(m => ({ Component: m.PlotsPage })) },
          { path: 'specs', lazy: () => import('./pages/SpecsListPage').then(m => ({ Component: m.SpecsListPage })) },
          { path: 'libraries', lazy: () => import('./pages/LibrariesPage').then(m => ({ Component: m.LibrariesPage })) },
          { path: 'map', lazy: () => import('./pages/MapPage').then(m => ({ Component: m.MapPage })) },
          { path: 'palette', lazy: () => import('./pages/PalettePage').then(m => ({ Component: m.PalettePage })) },
          { path: 'about', lazy: () => import('./pages/AboutPage').then(m => ({ Component: m.AboutPage })) },
          { path: 'legal', lazy: () => import('./pages/LegalPage').then(m => ({ Component: m.LegalPage })) },
          { path: 'mcp', lazy: () => import('./pages/McpPage').then(m => ({ Component: m.McpPage })) },
          { path: 'stats', lazy: () => import('./pages/StatsPage').then(m => ({ Component: m.StatsPage })) },
          { path: 'debug', lazy: () => import('./pages/DebugPage').then(m => ({ Component: m.DebugPage })) },
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
