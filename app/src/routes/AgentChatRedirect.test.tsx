import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AgentChatRedirect } from 'src/routes/AgentChatRedirect';

function Location() {
  const { pathname, search } = useLocation();
  return <output data-testid="location">{`${pathname}${search}`}</output>;
}

function renderAt(url: string) {
  const router = createMemoryRouter(
    [
      { path: '/debug/agent', element: <AgentChatRedirect /> },
      { path: '/agent', element: <Location /> },
    ],
    { initialEntries: [url] }
  );
  render(<RouterProvider router={router} />);
  return router;
}

describe('AgentChatRedirect', () => {
  it('sends an old admin link to the one chat page, with what the page reads', () => {
    const router = renderAt(
      '/debug/agent?spec=scatter-basic&library=seaborn&language=python&source=plot_page&all=1'
    );
    // The fan-out's old `&all=1` stays behind: the page reads it no more.
    expect(screen.getByTestId('location')).toHaveTextContent(
      /^\/agent\?spec=scatter-basic&library=seaborn&language=python&source=plot_page$/
    );
    // In place of the old address, so the back button does not bounce through it.
    expect(router.state.historyAction).toBe('REPLACE');
  });

  it('sends a bare old address to the bare chat page', () => {
    renderAt('/debug/agent');
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/agent$/);
  });
});
