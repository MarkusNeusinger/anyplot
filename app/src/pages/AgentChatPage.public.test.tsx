/**
 * The chat at `/agent` on the public lane: a visitor's page, and an admin's in "view as
 * visitor". It opens only while the API's public lane is open, talks to `/agent/*`
 * anonymously (the tab id and the session id as headers, no cookie, no admin token), says it
 * is experimental above the first input, and records the open. A visitor's browser never asks
 * the debug API and shows no admin menu. The page's flows are in AgentChatPage.test.tsx (on
 * the admin lane); this file stubs only what the lane changes, and
 * AgentChatPage.parity.test.tsx compares the two lanes' DOM.
 */

import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { analyticsMuted } from 'src/analytics/mute';
import { resetAgentLaneProbe } from 'src/hooks/useAgentLaneOpen';
import { AgentChatPage, HIGHCHARTS_NOTE } from 'src/pages/AgentChatPage';
import { AGENT_INTRO_DESCRIPTION, AGENT_INTRO_TITLE } from 'src/sections/agent-chat/AgentIntro';
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

function renderPath(path: string) {
  const router = createMemoryRouter([{ path: '/agent', element: <AgentChatPage /> }], {
    initialEntries: [path],
  });
  const view = render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
  return { ...view, router };
}

function renderPage(library = 'matplotlib', language = 'python', extra = '') {
  return renderPath(`/agent?spec=scatter-basic&library=${library}&language=${language}${extra}`);
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

  it.each(['spec_hub', 'plot_page', 'plot_of_the_day', 'agent_intro'])(
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

  it("explains the chat to a visitor at /agent without a plot, and asks nothing but the lane's door", async () => {
    renderPath('/agent');
    const intro = await screen.findByTestId('agent-intro');
    await waitFor(() => expect(document.title).toBe('use with my data | anyplot.ai'));
    expect(document.querySelector('meta[name="description"]')).toHaveAttribute(
      'content',
      expect.stringContaining("an agent adapts that plot's code to your columns")
    );
    // The page's own Open Graph pair replaces the home page's shell defaults in the head.
    expect(AGENT_INTRO_TITLE).toBe('use with my data | anyplot.ai');
    const og = (property: string) =>
      Array.from(document.querySelectorAll(`meta[property="${property}"]`)).map(meta =>
        meta.getAttribute('content')
      );
    expect(og('og:title')).toEqual([AGENT_INTRO_TITLE]);
    expect(og('og:description')).toEqual([AGENT_INTRO_DESCRIPTION]);
    // Never indexed, so no canonical either.
    expect(document.querySelector('link[rel="canonical"]')).toBeNull();
    // A tool page, never one to index, also as the explainer.
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      'content',
      'noindex, nofollow'
    );
    expect(within(intro).getByRole('link', { name: 'pick any plot' })).toHaveAttribute(
      'href',
      '/plots'
    );
    expect(within(intro).getByRole('link', { name: 'Browse plots' })).toHaveAttribute(
      'href',
      '/plots'
    );
    // One example per language, each opening the chat on its pair with the explainer's source.
    const examples = within(
      within(intro).getByRole('list', { name: 'or start with' })
    ).getAllByRole('listitem');
    expect(examples).toHaveLength(3);
    [
      ['scatter-basic', 'matplotlib', 'python'],
      ['bar-basic', 'ggplot2', 'r'],
      ['line-basic', 'd3', 'javascript'],
    ].forEach(([spec, library, language], index) => {
      const item = examples[index];
      expect(within(item).getByRole('link', { name: `${spec} in ${library}` })).toHaveAttribute(
        'href',
        `/agent?spec=${spec}&library=${library}&language=${language}&source=agent_intro`
      );
      expect(within(item).getByText(language)).toBeInTheDocument();
    });
    // Text and links only: no session, no status read, no debug call, no `agent_open`.
    expect(calls.map(call => call.url.pathname)).toEqual(['/agent/lane']);
    expect(analytics.trackEvent).not.toHaveBeenCalled();
    expect(screen.queryByTestId('experimental-notice')).not.toBeInTheDocument();
  });

  it('records one open per chat picked on the explainer, also after going back to it', async () => {
    const user = userEvent.setup();
    const { router } = renderPath('/agent');
    const opens = () =>
      analytics.trackEvent.mock.calls.filter(([name]) => name === 'agent_open').map(([, p]) => p);

    await user.click(await screen.findByRole('link', { name: 'scatter-basic in matplotlib' }));
    await screen.findByLabelText('Message');
    await waitFor(() => expect(router.state.location.search).not.toContain('source='));
    expect(opens()).toEqual([
      { library: 'matplotlib', source: 'agent_intro', spec: 'scatter-basic' },
    ]);

    await act(() => router.navigate(-1));
    await user.click(await screen.findByRole('link', { name: 'line-basic in d3' }));
    await waitFor(() => expect(opens()).toHaveLength(2));
    expect(opens()[1]).toEqual({ library: 'd3', source: 'agent_intro', spec: 'line-basic' });
    // The source leaves the address again, so a reload of it counts as a direct open.
    await waitFor(() =>
      expect(router.state.location.search).toBe('?spec=line-basic&library=d3&language=javascript')
    );
  });

  it('records a chat reached straight from another chat by a history jump as an open of its own', async () => {
    const user = userEvent.setup();
    const { router } = renderPath('/agent');
    const opens = () =>
      analytics.trackEvent.mock.calls.filter(([name]) => name === 'agent_open').map(([, p]) => p);
    const sessions = () =>
      calls.filter(
        call => call.url.pathname.endsWith('/agent/sessions') && call.init.method === 'POST'
      );

    await user.click(await screen.findByRole('link', { name: 'scatter-basic in matplotlib' }));
    await screen.findByLabelText('Message');
    await waitFor(() => expect(router.state.location.search).not.toContain('source='));
    await act(() => router.navigate('/agent'));
    await user.click(await screen.findByRole('link', { name: 'line-basic in d3' }));
    await waitFor(() => expect(opens()).toHaveLength(2));
    await waitFor(() => expect(router.state.location.search).not.toContain('source='));

    // From chat B straight back to chat A, a pair in the address the whole way: a new chat.
    await act(() => router.navigate(-2));
    expect(router.state.location.search).toBe(
      '?spec=scatter-basic&library=matplotlib&language=python'
    );
    await waitFor(() => expect(sessions()).toHaveLength(3));
    await waitFor(() => expect(opens()).toHaveLength(3));
    expect(opens()).toEqual([
      { library: 'matplotlib', source: 'agent_intro', spec: 'scatter-basic' },
      { library: 'd3', source: 'agent_intro', spec: 'line-basic' },
      { library: 'matplotlib', source: 'direct', spec: 'scatter-basic' },
    ]);
  });

  it('records no second open for a library switch inside the chat', async () => {
    const user = userEvent.setup();
    answerWith(
      '/specs/scatter-basic',
      json(200, {
        title: 'Basic Scatter Plot',
        implementations: ['matplotlib', 'seaborn', 'highcharts'].map(library_id => ({
          library_id,
        })),
      })
    );
    answerWith(
      '/agent/session/library',
      json(200, { session_id: 'S1', eligibility: { eligible: true, status: 'clean', reasons: [] } })
    );
    const { router } = renderPage();
    await screen.findByLabelText('Message');
    await waitFor(() => expect(screen.getByTestId('language-chip')).toBeEnabled());

    await user.click(screen.getByRole('button', { name: /^Library: matplotlib/ }));
    const option = await within(await screen.findByRole('dialog')).findByRole('button', {
      name: 'seaborn',
    });
    await waitFor(() => expect(option).toBeEnabled());
    await user.click(option);
    await waitFor(() => expect(router.state.location.search).toContain('library=seaborn'));
    expect(
      analytics.trackEvent.mock.calls.filter(([name]) => name === 'agent_open').map(([, p]) => p)
    ).toEqual([{ library: 'matplotlib', source: 'direct', spec: 'scatter-basic' }]);
  });

  it('says the assistant is closed at /agent without a plot while the lane is, with no explainer', async () => {
    laneOpen = false;
    renderPath('/agent');
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    expect(screen.queryByTestId('agent-intro')).not.toBeInTheDocument();
    expect(calls.every(call => call.url.pathname.endsWith('/agent/lane'))).toBe(true);
  });

  it.each([
    ['/agent', 'without a plot'],
    ['/agent?spec=scatter-basic&library=matplotlib&language=python', 'at a chat address'],
  ])(
    'keeps the terms of use under the closed notice at %s (%s), and asks nothing but the lane',
    async path => {
      // `/agent` is where the terms live, so they stand there also while the assistant is paused.
      laneOpen = false;
      renderPath(path);
      await screen.findByText(/the assistant is closed right now/);
      const terms = screen.getByTestId('agent-intro-terms');
      // Below the notice's sentence, whose last link is the way on to the catalogue.
      const catalogue = screen.getByRole('link', { name: 'catalogue' });
      expect(
        catalogue.compareDocumentPosition(terms) & Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy();
      // Under the same heading and in the same order as on the explainer.
      expect(terms.previousElementSibling).toBe(
        screen.getByRole('heading', { level: 3, name: 'ground rules' })
      );
      expect(
        within(terms)
          .getAllByRole('term')
          .map(label => label.textContent)
      ).toEqual(['your code', 'privacy', 'limits', 'status']);
      expect(
        within(terms)
          .getAllByRole('definition')
          .map(text => text.textContent)
      ).toEqual([
        'yours to use, as is. Highcharts needs a licence from Highsoft for commercial use.',
        'what is stored, where and for how long',
        'use it only with data you may share, never for unlawful content or automated requests. daily limits apply per tab and per network; a misuse can pause you for the day.',
        'experimental, without warranty: results can be wrong and nobody checks them by hand. the operator may pause it at any time.',
      ]);
      expect(
        within(terms).getByRole('link', { name: 'what is stored, where and for how long' })
      ).toHaveAttribute('href', '/legal#assistant');
      // Text and links only: no session, no status read, while the door is closed.
      expect(calls.map(call => call.url.pathname)).toEqual(['/agent/lane']);
    }
  );

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
