import { act, render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';

import { agentChatRedirect, specLanguageRedirect } from 'src/routes/redirects';
import { ADMIN_HINT_KEY, readAdminHint } from 'src/utils/adminAuth';

/** The destination's stand-in: where the redirect lands, and the hint it finds when it mounts. */
function Landing() {
  const { pathname, search } = useLocation();
  return (
    <>
      <output data-testid="location">{`${pathname}${search}`}</output>
      <output data-testid="hint">{readAdminHint() ? 'admin hint' : 'no hint'}</output>
    </>
  );
}

/** The router as the app builds it for these addresses, started at `urls` (the last is open). */
function renderAt(...urls: string[]) {
  const router = createMemoryRouter(
    [
      { path: '/', element: <Landing /> },
      { path: '/debug/agent', loader: agentChatRedirect },
      { path: '/agent', element: <Landing /> },
      { path: '/:specId', element: <Landing /> },
      { path: '/:specId/:language', loader: specLanguageRedirect },
    ],
    { initialEntries: urls }
  );
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
