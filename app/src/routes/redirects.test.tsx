import { useEffect } from 'react';

import { act, render, screen, waitFor } from '@testing-library/react';
import {
  createBrowserRouter,
  createMemoryRouter,
  type DataRouter,
  RouterProvider,
  useLocation,
} from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import {
  agentChatRedirect,
  legalMovedSectionRedirect,
  specLanguageRedirect,
} from 'src/routes/redirects';
import { ADMIN_HINT_KEY, readAdminHint } from 'src/utils/adminAuth';

/** Every address a page was rendered at, in order. */
let rendered: string[] = [];

/** The destination's stand-in: where the redirect lands, and the hint it finds when it mounts. */
function Landing() {
  const { pathname, search, hash } = useLocation();
  const address = `${pathname}${search}${hash}`;
  useEffect(() => {
    rendered.push(address);
  }, [address]);
  return (
    <>
      <output data-testid="location">{address}</output>
      <output data-testid="hint">{readAdminHint() ? 'admin hint' : 'no hint'}</output>
    </>
  );
}

/** The routes as the app builds them for these addresses. */
function routes() {
  return [
    { path: '/', element: <Landing /> },
    { path: '/debug/agent', loader: agentChatRedirect },
    { path: '/agent', element: <Landing /> },
    { path: '/legal', loader: legalMovedSectionRedirect, element: <Landing /> },
    { path: '/about', element: <Landing /> },
    { path: '/:specId', element: <Landing /> },
    { path: '/:specId/:language', loader: specLanguageRedirect },
  ];
}

/** Browser routers stay subscribed to the window's history until disposed. */
let browserRouters: DataRouter[] = [];

/**
 * The app's router on the window's own history, as a visitor has it after opening `before` and
 * then `url` in the address bar: the browser has written both entries before the app starts.
 */
function openInBrowser(before: string, url: string) {
  window.history.pushState(null, '', before);
  window.history.pushState(null, '', url);
  const entries = window.history.length;
  const router = createBrowserRouter(routes());
  browserRouters.push(router);
  render(<RouterProvider router={router} />);
  return { router, entries };
}

/** The router as the app builds it for these addresses, started at `urls` (the last is open). */
function renderAt(...urls: string[]) {
  const router = createMemoryRouter(routes(), { initialEntries: urls });
  // Every address that became a page: a redirect's own address must never be among them.
  const pages = [router.state.location.pathname];
  router.subscribe(state => {
    if (state.navigation.state === 'idle') pages.push(state.location.pathname);
  });
  render(<RouterProvider router={router} />);
  return { router, pages };
}

beforeEach(() => {
  localStorage.clear();
  rendered = [];
});

afterEach(() => {
  for (const router of browserRouters) router.dispose();
  browserRouters = [];
  window.history.replaceState(null, '', '/');
});

describe('legalMovedSectionRedirect', () => {
  // A loader's request carries no fragment, so the loader reads the address bar: on a fresh load
  // that is the address being opened.
  it('sends a fresh load of /legal#transparency to the about page, which is the only page', async () => {
    window.history.replaceState(null, '', '/legal#transparency');
    renderAt('/legal#transparency');
    expect(await screen.findByTestId('location')).toHaveTextContent(/^\/about#transparency$/);
    // The layout records a pageview for every page it renders (`RootLayout`): /legal is none.
    // The stand-in records in an effect, which can run after the text is already in the document,
    // so the list is waited for; once it holds the page, it must hold nothing else.
    await waitFor(() => expect(rendered).toEqual(['/about#transparency']));
  });

  it('leaves the legal page itself, and its other sections, where they are', async () => {
    window.history.replaceState(null, '', '/legal#assistant');
    renderAt('/legal#assistant');
    expect(await screen.findByTestId('location')).toHaveTextContent(/^\/legal#assistant$/);
  });

  it('lets the footer lead from /about#transparency to /legal: the bar still shows the page left', async () => {
    window.history.replaceState(null, '', '/about#transparency');
    const { router } = renderAt('/about#transparency');
    await act(() => router.navigate('/legal'));
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/legal$/);
  });
});

describe('agentChatRedirect', () => {
  it('sends an old admin link to the one chat page, with what the page reads', async () => {
    renderAt(
      '/debug/agent?spec=scatter-basic&library=seaborn&language=python&source=plot_page&all=1'
    );
    // The fan-out's old `&all=1` stays behind: the page reads it no more.
    expect(await screen.findByTestId('location')).toHaveTextContent(
      /^\/agent\?spec=scatter-basic&library=seaborn&language=python&source=plot_page$/
    );
  });

  it('sends a bare old address to the bare chat page', async () => {
    renderAt('/debug/agent');
    expect(await screen.findByTestId('location')).toHaveTextContent(/^\/agent$/);
  });

  it('sets the admin hint before the chat mounts: Access let this browser through /debug*', async () => {
    // A fresh browser, cleared storage, or a refusal that cleared the hint: still the admin's
    // bookmark, so the chat checks the admin lane instead of opening a visitor's page.
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull();
    renderAt('/debug/agent?spec=scatter-basic&library=matplotlib&language=python');
    expect(await screen.findByTestId('hint')).toHaveTextContent('admin hint');
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBe('1');
  });

  it('never becomes a page: the visitor goes from the page they were on to the chat, and back', async () => {
    const { router, pages } = renderAt('/');
    await act(() => router.navigate('/debug/agent?spec=scatter-basic&library=matplotlib'));
    expect(screen.getByTestId('location')).toHaveTextContent(
      /^\/agent\?spec=scatter-basic&library=matplotlib$/
    );
    // The layout records a pageview for every address that becomes a page (`RootLayout`).
    expect(pages).not.toContain('/debug/agent');
    // No history entry of its own, so the back button does not bounce through it.
    await act(() => router.navigate(-1));
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/);
  });
});

describe('specLanguageRedirect', () => {
  it("sends a language address to the spec hub, scoped to that language, as the hub's own query", async () => {
    renderAt('/scatter-basic/python');
    expect(await screen.findByTestId('location')).toHaveTextContent(
      /^\/scatter-basic\?language=python$/
    );
  });

  it('never becomes a page, from a link inside the app either (the breadcrumb)', async () => {
    const { router, pages } = renderAt('/');
    await act(() => router.navigate('/scatter-basic/r'));
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/scatter-basic\?language=r$/);
    expect(pages).not.toContain('/scatter-basic/r');
    await act(() => router.navigate(-1));
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/);
  });

  it('keeps a language with characters a query cannot hold as they are', async () => {
    renderAt('/scatter-basic/c%2B%2B');
    expect(await screen.findByTestId('location')).toHaveTextContent(
      /^\/scatter-basic\?language=c%2B%2B$/
    );
  });
});

describe('a redirect leaves no history entry of the old address', () => {
  // Pushed on top of the old address, the destination would leave Back one step short of the
  // page the visitor came from: Back would land on the old address and be sent forward again.
  it.each([
    ['/legal#transparency', '/about#transparency'],
    [
      '/debug/agent?spec=scatter-basic&library=matplotlib&language=python',
      '/agent?spec=scatter-basic&library=matplotlib&language=python',
    ],
    ['/scatter-basic/python', '/scatter-basic?language=python'],
    // The bar and the loader's request must agree on a percent-encoded path too.
    ['/scatter-basic/c%2B%2B', '/scatter-basic?language=c%2B%2B'],
  ])('a fresh load of %s takes over its entry, and Back leaves the page', async (old, to) => {
    const { entries } = openInBrowser('/stats', old);
    expect(await screen.findByTestId('location')).toHaveTextContent(to);
    const { pathname, search, hash } = window.location;
    expect(`${pathname}${search}${hash}`).toBe(to);
    expect(window.history.length).toBe(entries);

    act(() => window.history.back());
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/stats$/));
    expect(window.location.pathname).toBe('/stats');
  });

  it.each([
    [
      '/debug/agent?spec=scatter-basic&library=matplotlib&language=python',
      '/agent?spec=scatter-basic&library=matplotlib&language=python',
    ],
    ['/scatter-basic/python', '/scatter-basic?language=python'],
  ])('a link inside the app to %s keeps the page it leaves, one Back away', async (old, to) => {
    const { router, entries } = openInBrowser('/', '/stats');
    expect(await screen.findByTestId('location')).toHaveTextContent(/^\/stats$/);
    await act(() => router.navigate(old));
    expect(screen.getByTestId('location')).toHaveTextContent(to);
    expect(window.history.length).toBe(entries + 1);

    act(() => window.history.back());
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/stats$/));
  });
});
