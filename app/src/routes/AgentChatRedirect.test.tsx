import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';

import { AgentChatRedirect } from 'src/routes/AgentChatRedirect';
import { ADMIN_HINT_KEY, readAdminHint } from 'src/utils/adminAuth';

/** The chat page's stand-in: where the redirect lands, and the hint it finds when it mounts. */
function Landing() {
  const { pathname, search } = useLocation();
  return (
    <>
      <output data-testid="location">{`${pathname}${search}`}</output>
      <output data-testid="hint">{readAdminHint() ? 'admin hint' : 'no hint'}</output>
    </>
  );
}

function renderAt(url: string) {
  const router = createMemoryRouter(
    [
      { path: '/debug/agent', element: <AgentChatRedirect /> },
      { path: '/agent', element: <Landing /> },
    ],
    { initialEntries: [url] }
  );
  render(<RouterProvider router={router} />);
  return router;
}

beforeEach(() => {
  localStorage.clear();
});

describe('AgentChatRedirect', () => {
  it('sends an old admin link to the one chat page, with what the page reads', async () => {
    const router = renderAt(
      '/debug/agent?spec=scatter-basic&library=seaborn&language=python&source=plot_page&all=1'
    );
    // The fan-out's old `&all=1` stays behind: the page reads it no more.
    expect(await screen.findByTestId('location')).toHaveTextContent(
      /^\/agent\?spec=scatter-basic&library=seaborn&language=python&source=plot_page$/
    );
    // In place of the old address, so the back button does not bounce through it.
    expect(router.state.historyAction).toBe('REPLACE');
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
});
