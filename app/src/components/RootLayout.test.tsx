import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { MemoryRouter, Routes, Route, Link } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

const { setAmbient } = vi.hoisted(() => ({ setAmbient: vi.fn() }));

vi.mock('../hooks/useAnalytics', async () => {
  const actual = await vi.importActual<typeof import('../hooks/useAnalytics')>('../hooks/useAnalytics');
  return { ...actual, setAnalyticsAmbientProps: setAmbient };
});

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }),
    useLatestRelease: () => null,
  };
});

vi.mock('../hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('../hooks/useLayoutContext')>('../hooks/useLayoutContext');
  return { ...actual, useTheme: () => ({ isDark: true, toggle: vi.fn() }) };
});

vi.mock('./MastheadRule', () => ({ MastheadRule: () => <div data-testid="masthead" /> }));
vi.mock('./NavBar', () => ({ NavBar: () => <div data-testid="navbar" /> }));
vi.mock('./Footer', () => ({ Footer: () => <div data-testid="footer" /> }));

import { RootLayout } from './RootLayout';

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
    </ThemeProvider>,
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
