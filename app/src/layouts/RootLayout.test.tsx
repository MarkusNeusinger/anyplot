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
vi.mock('src/components/FeedbackWidget', () => ({
  FeedbackWidget: () => <div data-testid="feedback-widget" />,
}));

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
            <Route path="/agent" element={<div>agent-page</div>} />
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

  const siteFeedback = () => document.querySelector('[data-testid="feedback-widget"]') !== null;

  it("shows the site's feedback button everywhere but in the agent chat", () => {
    // The chat has feedback rows of its own; on a phone the button covered `.send()`.
    // One chat page for visitors and admins; `/debug/agent` only redirects there in its loader.
    const { unmount } = renderAt('/');
    expect(siteFeedback()).toBe(true);
    unmount();
    const view = renderAt('/agent?spec=scatter-basic&library=matplotlib&language=python');
    expect(view.getByText('agent-page')).toBeInTheDocument();
    expect(siteFeedback()).toBe(false);
  });

  it('hides it in a chat also with a trailing slash or without the language', () => {
    for (const address of [
      '/agent/?spec=scatter-basic&library=matplotlib&language=python',
      '/agent?spec=line-basic&library=d3',
      '/agent?library=ggplot2&spec=bar-basic&source=agent_intro',
    ]) {
      const { unmount } = renderAt(address);
      expect(siteFeedback(), address).toBe(false);
      unmount();
    }
  });

  it("shows it on the explainer, wherever the query names no catalogue pair, as the page's rule", () => {
    // The page shows the explainer for each of these (`namesAgentChat`), and the explainer has
    // no feedback of its own.
    for (const address of [
      '/agent',
      '/agent/',
      '/agent?spec=scatter-basic',
      '/agent?spec=scatter-basic&library=excel',
      '/agent?spec=Scatter_Basic&library=matplotlib',
      '/agent?library=matplotlib',
    ]) {
      const { unmount } = renderAt(address);
      expect(siteFeedback(), address).toBe(true);
      unmount();
    }
  });

  it('takes the button away as an example opens the chat, and brings it back on the way back', async () => {
    const user = userEvent.setup();
    const view = render(
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={['/agent']}>
          <Routes>
            <Route element={<RootLayout />}>
              <Route
                path="/agent"
                element={
                  <div>
                    <Link to="/agent?spec=scatter-basic&library=matplotlib&language=python">
                      open-chat
                    </Link>
                    <Link to="/agent">open-explainer</Link>
                  </div>
                }
              />
            </Route>
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
    expect(siteFeedback()).toBe(true);
    await user.click(view.getByText('open-chat'));
    expect(siteFeedback()).toBe(false);
    await user.click(view.getByText('open-explainer'));
    expect(siteFeedback()).toBe(true);
  });
});
