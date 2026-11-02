/**
 * The public chat at `/agent`: the same page on the public lane. It opens only while
 * the API's public lane is open, talks to `/agent/*` anonymously (the tab id and the
 * session id as headers, no cookie, no admin token), says it is experimental above
 * the first input, offers no `all`, and starts the data boxes unticked. The page's
 * flows are in AgentChatPage.test.tsx; this file stubs only what the lane changes.
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { resetAgentLaneProbe } from 'src/hooks/useAgentLaneOpen';
import { HIGHCHARTS_NOTE, PublicAgentChatPage } from 'src/pages/AgentChatPage';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    AGENT_CHAT_ENABLED: true,
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

let laneOpen: boolean;
let calls: { url: URL; init: RequestInit }[];

function stubFetch() {
  calls = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      calls.push({ url, init });
      const method = init.method ?? 'GET';
      if (url.pathname.endsWith('/agent/lane')) {
        return laneOpen ? json(200, { open: true }) : json(404, { detail: 'not enabled' });
      }
      if (url.pathname.endsWith('/agent/sessions') && method === 'POST') {
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      if (url.pathname.endsWith('/agent/status')) {
        return json(200, { libraries: ['matplotlib', 'seaborn', 'highcharts'], enabled: true });
      }
      if (method === 'DELETE') return new Response(null, { status: 204 });
      return json(404, { detail: 'not_found' });
    })
  );
}

function renderPage(library = 'matplotlib', language = 'python') {
  const router = createMemoryRouter([{ path: '/agent', element: <PublicAgentChatPage /> }], {
    initialEntries: [`/agent?spec=scatter-basic&library=${library}&language=${language}`],
  });
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  resetAgentLaneProbe();
  laneOpen = true;
  analytics.trackEvent.mockClear();
  analytics.trackPageview.mockClear();
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PublicAgentChatPage', () => {
  it('opens a session on the public lane, anonymously, and never on the admin one', async () => {
    // Even a browser with the admin hint stays on the public lane at /agent.
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderPage();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled());

    const open = calls.find(
      call => call.url.pathname.endsWith('/agent/sessions') && call.init.method === 'POST'
    );
    expect(open).toBeDefined();
    const headers = open!.init.headers as Record<string, string>;
    expect(headers['X-Anyplot-Anon']).toMatch(/^[A-Za-z0-9_-]{22,64}$/);
    expect(headers['X-Admin-Token']).toBeUndefined();
    expect(open!.init.credentials).toBe('omit');
    expect(calls.some(call => call.url.pathname.includes('/debug/'))).toBe(false);
    expect(analytics.trackPageview).toHaveBeenCalledWith('/agent');
  });

  it('says it is experimental above the first input, with the link to the legal page', async () => {
    renderPage();
    const notice = await screen.findByTestId('experimental-notice');
    expect(notice).toHaveTextContent(/# experimental/);
    expect(notice).toHaveTextContent(
      /Claude by Anthropic, through Google Cloud Vertex AI in the EU/
    );
    expect(notice).toHaveTextContent(/nobody checks them by hand/);
    expect(notice).toHaveTextContent(/nothing is stored unless you send feedback/);
    expect(notice).toHaveTextContent(/daily limits apply/);
    const link = within(notice).getByRole('link', { name: 'how the assistant works' });
    expect(link).toHaveAttribute('href', '/legal#assistant');
    expect(link).toHaveAttribute('target', '_blank');
    // Above the data card's paste box: the notice comes first in the document.
    const box = await screen.findByRole('textbox', { name: /data/i });
    expect(notice.compareDocumentPosition(box) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('offers no "all" and starts the .save() box unticked', async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled());
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).not.toBeChecked();

    await user.click(screen.getByRole('button', { name: /^Library: matplotlib/ }));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).queryByRole('button', { name: 'All libraries' })).toBeNull();
  });

  it('carries the Highcharts note while the session plots in Highcharts', async () => {
    renderPage('highcharts', 'javascript');
    expect(await screen.findByTestId('highcharts-licence')).toHaveTextContent(HIGHCHARTS_NOTE);
  });

  it('says the assistant is closed while the lane is, and opens nothing', async () => {
    laneOpen = false;
    renderPage();
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    expect(calls.every(call => call.url.pathname.endsWith('/agent/lane'))).toBe(true);
    expect(screen.queryByTestId('experimental-notice')).not.toBeInTheDocument();
  });
});
