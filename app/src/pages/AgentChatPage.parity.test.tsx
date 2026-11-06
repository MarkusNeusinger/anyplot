/**
 * The admin's chat is the visitors' (owner, 2026-11-06): one page, the same code, the same DOM,
 * so the owner never misses what a visitor meets. This test renders the page with the same
 * mocked session for a visitor (the public lane, `/agent/*`), for an admin (the admin lane,
 * `/debug/agent/*`) and for an admin in "view as visitor" (the public lane again), through the
 * states a session goes through, and compares each admin's DOM with the visitor's outside one
 * explicit allowlist:
 *
 * - the admin menu, the one admin-only element: everything marked `data-testid="admin-menu…"`,
 *   its button (`admin-menu`), its popover (`admin-menu-panel`) and, on the closed door's page,
 *   its row (`admin-menu-row`);
 * - the fan-out, but only while it is on: no state here turns it on, and the test checks so.
 *
 * Any other lane difference fails here. React's ids are numbered by first appearance, since the
 * admin menu takes ids of its own. With the public door closed the admin lane still opens, by
 * design, so that state compares the visitor's view only.
 */

import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { resetAgentLaneProbe } from 'src/hooks/useAgentLaneOpen';
import { AgentChatPage } from 'src/pages/AgentChatPage';
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

const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

function sse(events: [string, unknown][]) {
  return new Response(
    events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join(''),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
  );
}

const SUMMARY = '2 rows: hours and score, both numbers. Is hours the x axis?';
const DATASET = {
  preview: [
    ['1.5', '52'],
    ['2.0', '58'],
  ],
  profile: {
    rows: 2,
    columns: [
      { name: 'hours', dtype: 'number', missing: 0, unique: 2 },
      { name: 'score', dtype: 'integer', missing: 0, unique: 2 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  bindings: [
    { role: 'x', column: 'hours' },
    { role: 'y', column: 'score' },
  ],
  warnings: [],
  roles: ['x', 'y'].map(name => ({
    name,
    kinds: ['numeric'],
    required: true,
    variadic: false,
    description: `${name} values`,
  })),
  version: 1,
};
const PLOT = {
  status: 'ok',
  attempts: 1,
  artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
  changes: [],
  residual_defects: [],
  version: 1,
};

/** How the session's open answers, the same on both lanes. */
type Open = 'ok' | 'hold' | 'error' | 'ineligible';
let open: Open;
/** The public lane's door (`GET /agent/lane`). */
let door: boolean;

/**
 * One BFF for both lanes. A session route of the admin lane (`/debug/agent/sessions/S1/<rest>`)
 * and of the public lane (`/agent/session/<rest>`) answer alike, and so do the two `/status`.
 */
function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      const path = url.pathname;
      if (path.endsWith('/agent/lane')) {
        return door ? json(200, { open: true }) : json(404, { detail: 'not_enabled' });
      }
      if (path.endsWith('/specs/scatter-basic')) {
        return json(200, {
          title: 'Basic Scatter Plot',
          data: ['`x` (numeric) - the horizontal axis', '`y` (numeric) - the vertical axis'],
          implementations: ['matplotlib', 'seaborn'].map(library_id => ({ library_id })),
        });
      }
      if (path === '/debug/agent/status' || path === '/agent/status') {
        return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true, user_max_runs: 2 });
      }
      if ((path === '/debug/agent/sessions' || path === '/agent/sessions') && method === 'POST') {
        if (open === 'hold') return new Promise<Response>(() => undefined);
        if (open === 'error') return json(500, { detail: 'internal', ref: 'r-500' });
        if (open === 'ineligible') return json(422, { detail: 'not_eligible', ref: 'r-ne' });
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      const rest = path.match(/^\/debug\/agent\/sessions\/S1(\/.*)?$|^\/agent\/session(\/.*)?$/);
      if (!rest) return json(404, { detail: 'not_found' });
      const sub = rest[1] ?? rest[2] ?? '';
      if (method === 'DELETE' && sub === '') return new Response(null, { status: 204 });
      if (sub === '/dataset' && method === 'POST') return json(200, DATASET);
      if (sub === '/bindings' && method === 'PUT') {
        return json(200, {
          bindings: JSON.parse(String(init.body)),
          complete: true,
          missing_roles: [],
        });
      }
      if (sub === '/dataset/confirm') return json(200, { confirmed: true, rows: 2, columns: 2 });
      if (sub === '/messages') {
        const body = JSON.parse(String(init.body)) as { action?: string };
        return body.action === 'summarize_data'
          ? sse([
              ['message', { text: SUMMARY }],
              ['done', { llm_calls: 1 }],
            ])
          : sse([
              ['plot', PLOT],
              ['message', { text: 'Here is your plot.' }],
              ['done', { llm_calls: 2, data_confirmed: true }],
            ]);
      }
      if (sub === '/outcome') return new Response(null, { status: 204 });
      // The plot's files are not served: its card shows them as failed, alike on both lanes.
      return json(404, { detail: 'not_found' });
    })
  );
}

function renderPage() {
  const router = createMemoryRouter([{ path: '/agent', element: <AgentChatPage /> }], {
    initialEntries: ['/agent?spec=scatter-basic&library=matplotlib&language=python'],
  });
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

const turnEnded = () =>
  waitFor(() => expect(screen.queryByRole('button', { name: 'Stop' })).not.toBeInTheDocument());

/** Paste a table into the message box and send it: its summary comes back. */
async function pasteTable() {
  const box = await screen.findByLabelText('Message');
  await waitFor(() => expect(box).toBeEnabled());
  fireEvent.paste(box, {
    clipboardData: { files: [], getData: () => 'hours,score\n1.5,52\n2.0,58\n' },
  });
  await screen.findByRole('group', { name: /^Attached/ });
  fireEvent.keyDown(box, { key: 'Enter' });
  expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
  await turnEnded();
}

/** The table, then one `.create_plot()`: the first plot ships. */
async function plotOnce() {
  await pasteTable();
  const create = screen.getByRole('button', { name: 'Create plot' });
  await waitFor(() => expect(create).toBeEnabled());
  fireEvent.click(create);
  expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
  await turnEnded();
}

/** Who looks: a visitor, an admin on the admin lane, an admin in "view as visitor". */
type Who = 'visitor' | 'admin' | 'as visitor';

interface State {
  open: Open;
  reach: () => Promise<void>;
  /** The public door; open unless said. */
  door?: boolean;
  /** The admins compared with the visitor; both unless said. */
  compare?: readonly Exclude<Who, 'visitor'>[];
}

/** The states a session goes through, and how the page gets there. */
const STATES: Record<string, State> = {
  opening: {
    open: 'hold',
    reach: async () => {
      await screen.findByTestId('session-opening');
    },
  },
  'ready without data': {
    open: 'ok',
    reach: async () => {
      await waitFor(() => expect(screen.getByLabelText('Message')).toBeEnabled());
    },
  },
  'with data': { open: 'ok', reach: pasteTable },
  'with a plot': { open: 'ok', reach: plotOnce },
  // The feedback form unfolded: its data box and the consent line under it.
  'with the feedback form open': {
    open: 'ok',
    reach: async () => {
      await plotOnce();
      fireEvent.click(screen.getByRole('button', { name: 'Thumbs up' }));
      await screen.findByRole('link', { name: 'legal' });
    },
  },
  error: {
    open: 'error',
    reach: async () => {
      await screen.findByText(/^error · internal/);
    },
  },
  ineligible: {
    open: 'ineligible',
    reach: async () => {
      await screen.findByText('not eligible');
    },
  },
  // A popover of the page, in its portal as the admin menu's is.
  'with the library menu open': {
    open: 'ok',
    reach: async () => {
      const chip = await screen.findByTestId('library-chip');
      await waitFor(() => expect(chip).toBeEnabled());
      fireEvent.click(chip);
      await screen.findByRole('dialog', { name: 'Library of the plot' });
    },
  },
  // The closed door: the admin lane opens anyway, by design, so only the visitor's view compares.
  'with the public lane closed': {
    open: 'ok',
    door: false,
    compare: ['as visitor'],
    reach: async () => {
      await screen.findByText(/the assistant is closed right now/);
    },
  },
};

/** What may differ for an admin: the admin menu, everything marked `admin-menu…`. */
const ADMIN_ONLY = '[data-testid^="admin-menu"]';

/** The page's DOM without the admin-only elements, React's ids numbered by first appearance. */
function snapshot(): string {
  const body = document.body.cloneNode(true) as HTMLElement;
  for (const element of body.querySelectorAll(ADMIN_ONLY)) element.remove();
  const ids = new Map<string, string>();
  return body.innerHTML.replace(/_r_[0-9a-v]+_/g, id => {
    if (!ids.has(id)) ids.set(id, `_id${ids.size}_`);
    return ids.get(id)!;
  });
}

/** Let late answers land (the lists, an image that fails): two equal snapshots in a row. */
async function settled(): Promise<string> {
  let last = '';
  for (let round = 0; round < 20; round += 1) {
    await act(() => new Promise(resolve => setTimeout(resolve, 25)));
    const next = snapshot();
    if (next === last) return next;
    last = next;
  }
  throw new Error('the page did not settle');
}

async function pageFor(who: Who, state: string): Promise<string> {
  cleanup();
  localStorage.clear();
  sessionStorage.clear();
  resetAgentLaneProbe();
  if (who !== 'visitor') localStorage.setItem(ADMIN_HINT_KEY, '1');
  if (who === 'as visitor') sessionStorage.setItem(VIEW_AS_VISITOR_KEY, '1');
  open = STATES[state].open;
  door = STATES[state].door ?? true;
  stubFetch();
  renderPage();
  await STATES[state].reach();
  const dom = await settled();
  // The lane is the one asked for, and so is the admin menu.
  const calls = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls.map(
    ([input]) => new URL(String(input)).pathname
  );
  const opened = calls.filter(path => path.endsWith('/sessions') || path === '/agent/sessions');
  expect(opened.length > 0, `${who} opened no session`).toBe(door);
  expect(
    opened.every(path => path.startsWith('/debug/') === (who === 'admin')),
    `${who} opened ${opened.join(', ')}`
  ).toBe(true);
  if (who === 'visitor') {
    expect(screen.queryByTestId('admin-menu')).not.toBeInTheDocument();
    expect(calls.some(path => path.startsWith('/debug/'))).toBe(false);
  } else {
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(
      who === 'admin' ? /^admin ▾$/ : /^admin · as visitor ▾$/
    );
    // In the visitor's view the admin check is the one call to the debug API.
    if (who === 'as visitor') {
      expect(calls.filter(path => path.startsWith('/debug/'))).toEqual(['/debug/agent/status']);
    }
    // The fan-out is off: the only other allowed difference does not apply here.
    if (door) expect(screen.getByTestId('library-chip')).toHaveTextContent(/^matplotlib ▾$/);
    expect(
      within(document.body).queryByRole('button', { name: 'Plot in all libraries' })
    ).not.toBeInTheDocument();
  }
  return dom;
}

beforeEach(() => {
  URL.createObjectURL = vi.fn(() => 'blob:mock');
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('AgentChatPage lane parity', () => {
  it.each(Object.keys(STATES))(
    'shows a visitor and an admin the same page outside the admin menu: %s',
    async state => {
      const visitor = await pageFor('visitor', state);
      for (const who of STATES[state].compare ?? (['admin', 'as visitor'] as const)) {
        expect(await pageFor(who, state), `${who} differs`).toBe(visitor);
      }
    }
  );

  it('catches a difference outside the allowlist', async () => {
    // The check itself: one element only the admin's page has, anywhere but in the admin menu,
    // and the pages differ.
    const visitor = await pageFor('visitor', 'ready without data');
    await pageFor('admin', 'ready without data');
    expect(snapshot()).toBe(visitor);
    screen.getByTestId('library-chip').insertAdjacentHTML('afterend', '<span>admin only</span>');
    expect(snapshot()).not.toBe(visitor);
  });
});
