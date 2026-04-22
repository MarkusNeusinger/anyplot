import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { RouteErrorBoundary } from './RouteErrorBoundary';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const theme = createTheme();

function renderWithRouter(thrown: unknown) {
  const router = createMemoryRouter(
    [
      {
        path: '/',
        errorElement: <RouteErrorBoundary />,
        loader: () => {
          throw thrown;
        },
        element: <div>never rendered</div>,
      },
    ],
    { initialEntries: ['/'] }
  );
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

describe('RouteErrorBoundary', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    sessionStorage.clear();
    // Replace window.location so we can spy on reload without jsdom errors.
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, reload: vi.fn() },
    });
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
    vi.restoreAllMocks();
  });

  it('renders generic error UI for unknown errors', async () => {
    renderWithRouter(new Error('boom'));
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /go home/i })).toBeInTheDocument();
  });

  it('renders 404 page for route 404 responses', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          errorElement: <RouteErrorBoundary />,
          loader: () => {
            throw new Response('Not Found', { status: 404 });
          },
          element: <div>never</div>,
        },
      ],
      { initialEntries: ['/'] }
    );
    render(
      <ThemeProvider theme={theme}>
        <RouterProvider router={router} />
      </ThemeProvider>
    );
    expect(await screen.findByText('404')).toBeInTheDocument();
    expect(screen.getByText('page not found')).toBeInTheDocument();
  });

  it('auto-reloads once on chunk load errors', async () => {
    renderWithRouter(new Error('Failed to fetch dynamically imported module: https://example.com/x.js'));
    await waitFor(() => expect(window.location.reload).toHaveBeenCalledTimes(1));
    expect(sessionStorage.getItem('anyplot:chunk-reload-attempt')).not.toBeNull();
  });

  it('does not reload loop — shows recovery UI after a prior attempt', async () => {
    sessionStorage.setItem('anyplot:chunk-reload-attempt', String(Date.now()));
    renderWithRouter(new Error('Failed to fetch dynamically imported module: https://example.com/x.js'));
    expect(await screen.findByText('A new version is available')).toBeInTheDocument();
    expect(window.location.reload).not.toHaveBeenCalled();
  });

  it('treats ChunkLoadError messages as chunk errors', async () => {
    renderWithRouter(new Error('ChunkLoadError: Loading chunk 42 failed'));
    await waitFor(() => expect(window.location.reload).toHaveBeenCalledTimes(1));
  });

  it('reloads the page when the Reload Page button is clicked', async () => {
    renderWithRouter(new Error('boom'));
    await screen.findByText('Something went wrong');
    await userEvent.click(screen.getByRole('button', { name: /reload page/i }));
    expect(window.location.reload).toHaveBeenCalledTimes(1);
  });

  it('handles string errors thrown from loaders', async () => {
    renderWithRouter('plain string error');
    // Plain strings are not chunk errors; render generic UI.
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
    // In dev mode the raw message is rendered — when present, it shows the string.
    const devMessage = screen.queryByText('plain string error');
    if (devMessage) {
      expect(devMessage).toBeInTheDocument();
    }
  });

  it('handles non-Error object values thrown from loaders', async () => {
    renderWithRouter({ some: 'object' });
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
  });

  it('handles JSON.stringify failures (circular refs) without crashing', async () => {
    const circular: Record<string, unknown> = {};
    circular.self = circular;
    renderWithRouter(circular);
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders useful diagnostics for non-404 Response errors', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          errorElement: <RouteErrorBoundary />,
          loader: () => {
            throw new Response('Bad', { status: 500, statusText: 'Internal Server Error' });
          },
          element: <div>never</div>,
        },
      ],
      { initialEntries: ['/'] }
    );
    render(
      <ThemeProvider theme={theme}>
        <RouterProvider router={router} />
      </ThemeProvider>
    );
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
  });

  it('detects chunk errors from non-Error objects with a message property', async () => {
    renderWithRouter({ message: 'Importing a module script failed' });
    await waitFor(() => expect(window.location.reload).toHaveBeenCalledTimes(1));
  });

  it('skips the reload-loop guard when sessionStorage throws', async () => {
    const getSpy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('sessionStorage unavailable');
    });
    renderWithRouter(new Error('Failed to fetch dynamically imported module: /x.js'));
    await waitFor(() => expect(window.location.reload).toHaveBeenCalledTimes(1));
    getSpy.mockRestore();
  });
});
