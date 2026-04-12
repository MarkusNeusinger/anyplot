import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AppDataProvider, Layout } from './Layout';
import { AppDataContext } from '../hooks/useLayoutContext';
import { useContext } from 'react';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// jsdom does not have requestIdleCallback / cancelIdleCallback
vi.stubGlobal(
  'requestIdleCallback',
  vi.fn((cb: IdleRequestCallback) => {
    const id = setTimeout(() => cb({} as IdleDeadline), 0);
    return id as unknown as number;
  }),
);
vi.stubGlobal('cancelIdleCallback', vi.fn((id: number) => clearTimeout(id)));

const theme = createTheme();

function wrap(ui: React.ReactElement) {
  return render(ui, {
    wrapper: ({ children }) => (
      <ThemeProvider theme={theme}>
        <MemoryRouter>{children}</MemoryRouter>
      </ThemeProvider>
    ),
  });
}

describe('Layout', () => {
  it('renders children via Outlet', () => {
    // Layout uses <Outlet />, which renders nothing without route context,
    // but the wrapper itself renders without errors.
    wrap(<Layout />);

    // The main Box should be present
    const main = document.querySelector('main');
    expect(main).toBeInTheDocument();
  });
});

describe('AppDataProvider', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Re-stub after restoreAllMocks clears them
    vi.stubGlobal(
      'requestIdleCallback',
      vi.fn((cb: IdleRequestCallback) => {
        const id = setTimeout(() => cb({} as IdleDeadline), 0);
        return id as unknown as number;
      }),
    );
    vi.stubGlobal('cancelIdleCallback', vi.fn((id: number) => clearTimeout(id)));
  });

  it('provides context to children', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ specs: [], libraries: [], specs_count: 0, plots_count: 0, libraries_count: 0 }),
      }),
    );

    function Consumer() {
      const ctx = useContext(AppDataContext);
      return <div data-testid="ctx">{ctx ? 'has-context' : 'no-context'}</div>;
    }

    wrap(
      <AppDataProvider>
        <Consumer />
      </AppDataProvider>,
    );

    expect(screen.getByTestId('ctx')).toHaveTextContent('has-context');
  });

  it('calls fetch for /specs, /libraries, and /stats', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal('fetch', fetchMock);

    wrap(
      <AppDataProvider>
        <div>child</div>
      </AppDataProvider>,
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    const urls = fetchMock.mock.calls.map((c: unknown[]) => c[0] as string);
    expect(urls.some((u: string) => u.includes('/specs'))).toBe(true);
    expect(urls.some((u: string) => u.includes('/libraries'))).toBe(true);
    expect(urls.some((u: string) => u.includes('/stats'))).toBe(true);
  });

  it('handles fetch failure gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('Network error')),
    );

    wrap(
      <AppDataProvider>
        <div data-testid="child">still renders</div>
      </AppDataProvider>,
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Initial data load incomplete:',
        'Network error',
      );
    });

    expect(screen.getByTestId('child')).toHaveTextContent('still renders');
    consoleSpy.mockRestore();
  });
});
