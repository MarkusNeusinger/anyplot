import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import { AppDataProvider } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { NotFoundPage } from './pages/NotFoundPage';

const LazyFallback = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
    <CircularProgress size={32} />
  </Box>
);

const lazySpec = () => import('./pages/SpecPage').then(m => ({ Component: m.SpecPage, HydrateFallback: LazyFallback }));

// Minimal passthrough wrapper so child routes get an Outlet
function PassthroughLayout() {
  return <Outlet />;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <PassthroughLayout />,
    children: [
      { index: true, lazy: () => import('./pages/LandingPage').then(m => ({ Component: m.LandingPage })) },
      { path: 'plots', lazy: () => import('./pages/CatalogPage').then(m => ({ Component: m.CatalogPage })) },
      { path: 'specs', lazy: () => import('./pages/SpecsListPage').then(m => ({ Component: m.SpecsListPage })) },
      { path: 'palette', lazy: () => import('./pages/PalettePage').then(m => ({ Component: m.PalettePage })) },
      { path: 'legal', lazy: () => import('./pages/LegalPage').then(m => ({ Component: m.LegalPage })) },
      { path: 'mcp', lazy: () => import('./pages/McpPage').then(m => ({ Component: m.McpPage })) },
      { path: 'stats', lazy: () => import('./pages/StatsPage').then(m => ({ Component: m.StatsPage })) },
      { path: 'python/:specId', lazy: lazySpec },
      { path: 'python/:specId/:library', lazy: lazySpec },
      { path: 'python/interactive/:specId/:library', lazy: () => import('./pages/InteractivePage').then(m => ({ Component: m.InteractivePage })) },
      { path: 'debug', lazy: () => import('./pages/DebugPage').then(m => ({ Component: m.DebugPage })) },
      { path: '*', element: <NotFoundPage /> },
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
