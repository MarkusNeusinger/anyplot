/**
 * The chat at `/agent` on the public lane: a visitor's page, and an admin's in "view as
 * visitor". It opens only while the API's public lane is open, talks to `/agent/*`
 * anonymously (the tab id and the session id as headers, no cookie, no admin token), says it
 * is experimental above the first input, and records the open. A visitor's browser never asks
 * the debug API and shows no admin menu. The page's flows are in AgentChatPage.test.tsx (on
 * the admin lane); this file stubs only what the lane changes, and
 * AgentChatPage.parity.test.tsx compares the two lanes' DOM.
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { analyticsMuted } from 'src/analytics/mute';
import { resetAgentLaneProbe } from 'src/hooks/useAgentLaneOpen';
import { AgentChatPage, HIGHCHARTS_NOTE } from 'src/pages/AgentChatPage';
import { EXPERIMENTAL_DETAILS, EXPERIMENTAL_LINE } from 'src/sections/agent-chat/lane';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY, VIEW_AS_VISITOR_KEY } from 'src/utils/adminAuth';

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    AGENT_CHAT_ENABLED: true,
    CONFIG: { ...actual.CONFIG, isDev: false, features: { agentChat: true } },
  };
});

const analytics = vi.hoisted(() => ({ trackEvent: vi.fn() }));
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

function renderPage(library = 'matplotlib', language = 'python', extra = '') {
  const router = createMemoryRouter([{ path: '/agent', element: <AgentChatPage /> }], {
    initialEntries: [`/agent?spec=scatter-basic&library=${library}&language=${language}${extra}`],
  });
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

/** One route's answer in place of the stub's, every other route as before. */
function answerWith(pathname: string, response: Response) {
  const stub = globalThis.fetch as unknown as ReturnType<
    typeof vi.fn<(input: string, init?: RequestInit) => Promise<Response>>
  >;
  const base = stub.getMockImplementation()!;
  stub.mockImplementation(async (input, init) =>
    new URL(input).pathname === pathname ? response.clone() : base(input, init)
  );
}

/** The calls to the debug API: a visitor's browser makes none. */
const debugCalls = () => calls.filter(call => call.url.pathname.includes('/debug/'));
/** The chat's own calls, on the public lane. */
const publicCalls = () => calls.filter(call => !call.url.pathname.includes('/debug/'));

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  resetAgentLaneProbe();
  laneOpen = true;
  analytics.trackEvent.mockClear();
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('AgentChatPage on the public lane', () => {
  it("opens a visitor's session on the public lane, anonymously, and never asks the debug API", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByTestId('language-chip')).toBeEnabled());

    const open = publicCalls().find(
      call => call.url.pathname.endsWith('/agent/sessions') && call.init.method === 'POST'
    );
    expect(open).toBeDefined();
    const headers = open!.init.headers as Record<string, string>;
    expect(headers['X-Anyplot-Anon']).toMatch(/^[A-Za-z0-9_-]{22,64}$/);
    expect(headers['X-Admin-Token']).toBeUndefined();
    expect(open!.init.credentials).toBe('omit');
    expect(debugCalls()).toEqual([]);
    // No admin menu, and nothing of it, for a visitor.
    expect(screen.queryByTestId('admin-menu')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    // A visitor's visit counts: the layout's pageview is not muted, and the open is recorded.
    expect(analyticsMuted()).toBe(false);
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
      library: 'matplotlib',
      source: 'direct',
      spec: 'scatter-basic',
    });
  });

  it.each(['spec_hub', 'plot_page', 'plot_of_the_day'])(
    "records a visitor's open from %s, then drops the source",
    async source => {
      renderPage('matplotlib', 'python', `&source=${source}`);
      await screen.findByLabelText('Message');
      expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
        library: 'matplotlib',
        source,
        spec: 'scatter-basic',
      });
    }
  );

  it('runs the public lane exactly for an admin in "view as visitor", and records nothing', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    sessionStorage.setItem(VIEW_AS_VISITOR_KEY, '1');
    renderPage();
    await waitFor(() => expect(screen.getByTestId('language-chip')).toBeEnabled());

    // The admin check only: every chat call goes to the public lane, as a visitor's does.
    expect(debugCalls().map(call => call.url.pathname)).toEqual(['/debug/agent/status']);
    const open = publicCalls().find(
      call => call.url.pathname.endsWith('/agent/sessions') && call.init.method === 'POST'
    );
    const headers = open!.init.headers as Record<string, string>;
    expect(headers['X-Anyplot-Anon']).toMatch(/^[A-Za-z0-9_-]{22,64}$/);
    expect(headers['X-Admin-Token']).toBeUndefined();
    expect(open!.init.credentials).toBe('omit');
    // The admin menu stays, with the way back and nothing the public lane does not have.
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · as visitor ▾$/);
    await userEvent.setup().click(screen.getByTestId('admin-menu'));
    const menu = await screen.findByRole('dialog', { name: 'Admin' });
    expect(
      within(menu)
        .getAllByRole('button')
        .map(button => button.textContent)
    ).toEqual(['view as visitor']);
    // The public lane has no `/budget`: the visitor's view has no meters and asks none.
    expect(within(menu).queryByTestId('admin-meters')).not.toBeInTheDocument();
    expect(calls.some(call => call.url.pathname.endsWith('/budget'))).toBe(false);
    // The owner's persona tests are no visitor's use: no pageview from the layout, no open.
    expect(analyticsMuted()).toBe(true);
    expect(analytics.trackEvent).not.toHaveBeenCalledWith('agent_open', expect.anything());
  });

  it("shows a visitor the service's mood from the public lane's status, and asks no budget", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByTestId('load-mood')).toHaveTextContent(/quiet$/));
    expect(calls.some(call => call.url.pathname.endsWith('/agent/status'))).toBe(true);
    expect(calls.some(call => call.url.pathname.endsWith('/budget'))).toBe(false);
  });

  it('shows no mood after a failed first read, never a guessed quiet', async () => {
    answerWith('/agent/status', json(503, { detail: 'unavailable' }));
    renderPage();
    await waitFor(() => expect(screen.getByTestId('language-chip')).toBeEnabled());
    expect(screen.getByTestId('chat-frame-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('load-mood')).not.toBeInTheDocument();
  });

  it('asks no budget for an expired admin session either', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    answerWith('/debug/agent/status', json(403, { detail: 'Invalid admin token' }));
    renderPage();
    await waitFor(() =>
      expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · expired ▾$/)
    );
    await userEvent.setup().click(screen.getByTestId('admin-menu'));
    const menu = await screen.findByRole('dialog', { name: 'Admin' });
    expect(within(menu).queryByTestId('admin-meters')).not.toBeInTheDocument();
    expect(calls.some(call => call.url.pathname.endsWith('/budget'))).toBe(false);
  });

  it('says it is an experimental AI in one line, with the details behind its button', async () => {
    const user = userEvent.setup();
    renderPage();
    const notice = await screen.findByTestId('experimental-notice');
    // In view without a click: an experimental AI (AI Act Art. 50) whose answers can be wrong,
    // one muted `//` line above the chat's frame since the v4 frame.
    expect(notice).toHaveTextContent(`// ${EXPERIMENTAL_LINE}`);
    expect(notice).toHaveTextContent(/^\/\/ experimental AI · answers can be wrong$/);
    expect(screen.queryByTestId('experimental-details')).not.toBeInTheDocument();
    // Above the message box, where the data comes in: the notice comes first in the document,
    // before the frame, and outside it.
    const box = await screen.findByRole('textbox', { name: 'Message' });
    const frame = screen.getByRole('region', { name: 'Chat' });
    expect(notice.compareDocumentPosition(box) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(notice.compareDocumentPosition(frame) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(frame).not.toContainElement(notice);

    const about = within(notice).getByRole('button', { name: 'About the assistant' });
    expect(about).toHaveAttribute('aria-expanded', 'false');
    await user.click(about);
    const dialog = await screen.findByRole('dialog', { name: 'About the assistant' });
    expect(about).toHaveAttribute('aria-expanded', 'true');
    // Where the chat lives and for how long first, then what is saved, the model, the rest.
    expect(
      within(within(dialog).getByTestId('experimental-details'))
        .getAllByRole('listitem')
        .map(item => item.textContent)
    ).toEqual([...EXPERIMENTAL_DETAILS, 'how the assistant works']);
    expect(EXPERIMENTAL_DETAILS[0]).toBe(
      'your chat and data live only in server memory, deleted after an hour idle'
    );
    expect(dialog).toHaveTextContent(
      /Claude by Anthropic, via Google Cloud Vertex AI in the EU · not used for training/
    );
    const link = within(dialog).getByRole('link', { name: 'how the assistant works' });
    expect(link).toHaveAttribute('href', '/legal#assistant');
    expect(link).toHaveAttribute('target', '_blank');

    // Escape closes it and gives the focus back to the button.
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(about).toHaveFocus();
  });

  it('keeps the notice above the frame while the session opens, and the same line once it is open', async () => {
    let open!: () => void;
    const opened = new Promise<void>(resolve => {
      open = resolve;
    });
    const answer = globalThis.fetch as unknown as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string, init: RequestInit = {}) => {
        if (new URL(input).pathname.endsWith('/agent/sessions') && init.method === 'POST') {
          await opened;
        }
        return answer(input, init);
      })
    );
    renderPage();
    expect(await screen.findByTestId('session-opening')).toBeInTheDocument();
    // Before the first input exists: the notice stands, above the frame and outside it.
    const notice = screen.getByTestId('experimental-notice');
    const frame = screen.getByRole('region', { name: 'Chat' });
    expect(notice.compareDocumentPosition(frame) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(frame).not.toContainElement(notice);

    open();
    expect(await screen.findByRole('textbox', { name: 'Message' })).toBeInTheDocument();
    // One tree in every phase: the line stays the same element, and so does the frame.
    expect(screen.getByTestId('experimental-notice')).toBe(notice);
    expect(screen.getByRole('region', { name: 'Chat' })).toBe(frame);
  });

  it("offers a visitor the libraries only: the fan-out and .save() are the admin menu's", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(screen.getByTestId('language-chip')).toBeEnabled());
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: '# include data.csv' })).not.toBeInTheDocument();
    expect(calls.some(call => call.url.pathname.endsWith('/bundle'))).toBe(false);

    await user.click(screen.getByRole('button', { name: /^Library: matplotlib/ }));
    const dialog = await screen.findByRole('dialog');
    expect(
      within(dialog)
        .getAllByRole('button')
        .map(button => button.textContent)
    ).toEqual(['matplotlib', 'seaborn', 'highcharts']);
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
    // A tool on a catalogue pair, never a page to index: also while the lane is closed.
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      'content',
      'noindex, nofollow'
    );
  });

  it("keeps an admin's hint when the public lane refuses a session in the visitor view", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    sessionStorage.setItem(VIEW_AS_VISITOR_KEY, '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string, init: RequestInit = {}) => {
        const url = new URL(input);
        if (url.pathname.endsWith('/agent/lane')) return json(200, { open: true });
        if (url.pathname === '/agent/sessions' && init.method === 'POST') {
          return json(401, { detail: 'unauthorized', ref: 'r-u' });
        }
        return json(200, { libraries: ['matplotlib'], enabled: true });
      })
    );
    renderPage();
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    // The public lane's refusal says nothing about the admin: the admin lane's sign-in stands,
    // and the admin menu keeps the way back.
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBe('1');
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · as visitor ▾$/);
  });

  it('says why a network cannot open one more session', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string, init: RequestInit = {}) => {
        const url = new URL(input);
        if (url.pathname.endsWith('/agent/lane')) return json(200, { open: true });
        if (url.pathname.endsWith('/agent/sessions') && init.method === 'POST') {
          return json(429, { detail: 'session_limit', ref: 'r-s' });
        }
        return json(200, { libraries: ['matplotlib'], enabled: true });
      })
    );
    renderPage();
    expect(
      await screen.findByText(/too many chats are open from your network/)
    ).toBeInTheDocument();
  });

  it.each([
    [
      'bot_check_failed',
      403,
      /^error · bot_check_failedthe browser check did not go through · try again$/,
    ],
    ['bot_check_unavailable', 503, /the browser check is not available right now · try again$/],
  ])(
    'answers a refused bot check (%s) with one calm line and a retry',
    async (code, status, text) => {
      vi.stubGlobal(
        'fetch',
        vi.fn(async (input: string, init: RequestInit = {}) => {
          const url = new URL(input);
          if (url.pathname.endsWith('/agent/lane')) return json(200, { open: true });
          if (url.pathname.endsWith('/agent/sessions') && init.method === 'POST') {
            return json(status, { detail: code, ref: 'r-b' });
          }
          return json(200, { libraries: ['matplotlib'], enabled: true });
        })
      );
      renderPage();

      const alert = await screen.findByRole('alert');
      expect(alert).toHaveTextContent(text);
      // The session never opened, so a reload loses nothing and runs a fresh check.
      expect(within(alert).getByRole('button', { name: 'try again' })).toBeInTheDocument();
    }
  );
});
