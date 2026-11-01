/**
 * The chat page's `.save()` in the header: shown with a session, hidden without
 * one, and wired to the bundle download. The flows of the page are in
 * AgentChatPage.test.tsx; this file stubs only the calls the header needs.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AgentChatPage } from 'src/pages/AgentChatPage';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    CONFIG: { ...actual.CONFIG, isDev: false, features: { agentChat: true } },
  };
});

const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const PAGE = '/debug/agent?spec=scatter-basic&library=matplotlib&language=python';

let bundleSearch: string[];

/** `opened` holds the session's opening until it resolves. */
function stubFetch(openStatus = 200, opened: Promise<void> = Promise.resolve()) {
  bundleSearch = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      if (url.pathname.endsWith('/debug/agent/sessions') && method === 'POST') {
        await opened;
        return openStatus === 200
          ? json(200, {
              session_id: 'S1',
              eligibility: { eligible: true, status: 'clean', reasons: [] },
            })
          : json(openStatus, { detail: 'not_eligible', ref: 'r1' });
      }
      if (url.pathname.endsWith('/sessions/S1/bundle')) {
        bundleSearch.push(url.search);
        return json(200, { transcript: [], versions: [] });
      }
      if (url.pathname.endsWith('/debug/agent/status')) {
        return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true });
      }
      if (method === 'DELETE') return new Response(null, { status: 204 });
      return json(404, { detail: 'not_found' });
    })
  );
}

/** A data router, as in the app: the page's leave warning uses the router's blocker. */
function renderPage() {
  const router = createMemoryRouter([{ path: '/debug/agent', element: <AgentChatPage /> }], {
    initialEntries: [PAGE],
  });
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

let downloads: string[];

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem(ADMIN_HINT_KEY, '1');
  analytics.trackEvent.mockClear();
  downloads = [];
  URL.createObjectURL = vi.fn(() => 'blob:bundle');
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement
  ) {
    downloads.push(this.download);
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('AgentChatPage .save()', () => {
  it('saves the open session with and without the data file', async () => {
    const user = userEvent.setup();
    stubFetch();
    renderPage();
    // Disabled while the session opens; the page renders the header anew once it is open.
    expect(await screen.findByRole('button', { name: 'Save' })).toBeDisabled();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled());
    const save = screen.getByRole('button', { name: 'Save' });

    await user.click(save);
    await waitFor(() => expect(downloads).toEqual(['anyplot-session-S1.json']));
    await user.click(screen.getByRole('checkbox', { name: '# include data.csv' }));
    await user.click(save);

    await waitFor(() =>
      expect(bundleSearch).toEqual(['?include_data=true', '?include_data=false'])
    );
    await waitFor(() =>
      expect(downloads).toEqual(['anyplot-session-S1.json', 'anyplot-session-S1.json'])
    );
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_session_saved', {
      include_data: 'no',
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('locks the data box while the session opens, so the box shows what a save sends', async () => {
    let open!: () => void;
    stubFetch(
      200,
      new Promise<void>(resolve => {
        open = resolve;
      })
    );
    renderPage();
    // The page renders the header anew once the session is open; a choice made
    // while it opens would be lost there.
    expect(await screen.findByRole('checkbox', { name: '# include data.csv' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();

    open();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled());
    const box = screen.getByRole('checkbox', { name: '# include data.csv' });
    expect(box).toBeEnabled();
    expect(box).toBeChecked();
  });

  it('offers no .save() when the session could not open', async () => {
    stubFetch(422);
    renderPage();
    expect(await screen.findByText('not eligible · ref r1')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
  });
});
