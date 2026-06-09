import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createTheme, ThemeProvider } from '@mui/material/styles';

const { setAmbient } = vi.hoisted(() => ({ setAmbient: vi.fn() }));

vi.mock('src/hooks/useAnalytics', async () => {
  const actual =
    await vi.importActual<typeof import('src/hooks/useAnalytics')>('src/hooks/useAnalytics');
  return { ...actual, setAnalyticsAmbientProps: setAmbient };
});

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }),
    useLatestRelease: () => null,
  };
});

vi.mock('src/hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useLayoutContext')>(
    'src/hooks/useLayoutContext'
  );
  return {
    ...actual,
    useTheme: () => ({
      mode: 'dark' as const,
      effective: 'dark' as const,
      isDark: true,
      setMode: vi.fn(),
      cycle: vi.fn(),
    }),
  };
});

vi.mock('src/layouts/MastheadRule', () => ({
  MastheadRule: () => <div data-testid="masthead" />,
}));
vi.mock('src/layouts/NavBar', () => ({ NavBar: () => <div data-testid="navbar" /> }));
vi.mock('src/layouts/Footer', () => ({ Footer: () => <div data-testid="footer" /> }));

import { RootLayout } from 'src/layouts/RootLayout';

const theme = createTheme();

function renderAt(initialPath: string) {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route
              path="/"
              element={
                <div>
                  <Link to="/legal">go-legal</Link>
                  <Link to="/about#section">go-about-hash</Link>
                </div>
              }
            />
            <Route path="/legal" element={<div>legal-page</div>} />
            <Route path="/about" element={<div>about-page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ThemeProvider>
  );
}

describe('RootLayout', () => {
  let scrollSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    setAmbient.mockClear();
    scrollSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  });

  afterEach(() => {
    scrollSpy.mockRestore();
  });

  it('synchronously sets the theme ambient prop on render', () => {
    renderAt('/');
    expect(setAmbient).toHaveBeenCalledWith({ theme: 'dark' });
  });

  it('scrolls to top when navigating to a new path (PUSH)', async () => {
    const user = userEvent.setup();
    renderAt('/');
    scrollSpy.mockClear();

    await user.click(document.querySelector('a[href="/legal"]') as HTMLElement);

    expect(scrollSpy).toHaveBeenCalledWith(0, 0);
  });

  it('does not scroll to top when the destination has a hash anchor', async () => {
    const user = userEvent.setup();
    renderAt('/');
    scrollSpy.mockClear();

    await user.click(document.querySelector('a[href="/about#section"]') as HTMLElement);

    expect(scrollSpy).not.toHaveBeenCalledWith(0, 0);
  });
});
