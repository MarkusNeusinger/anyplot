/**
 * The admin's chat is the visitors' (owner, 2026-11-06): one page, the same code, the same DOM,
 * so the owner never misses what a visitor meets. This test renders the page with the same
 * mocked session for a visitor (the public lane, `/agent/*`), for an admin (the admin lane,
 * `/debug/agent/*`) and for an admin in "view as visitor" (the public lane again), through the
 * states a session goes through, and compares each admin's DOM with the visitor's outside one
 * explicit allowlist:
 *
 * - the admin menu, the one admin-only element: everything marked `data-testid="admin-menu…"`,
 *   which the test checks is exactly its button (`admin-menu`), its popover (`admin-menu-panel`)
 *   and, on the closed door's page, its row (`admin-menu-row`), each once (`ADMIN_ONLY_IDS`);
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
  can_undo: false,
  original_version: 1,
};
const PLOT = {
  status: 'ok',
  attempts: 1,
  artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
  changes: [],
  residual_defects: [],
  version: 1,
};
/** The message that asks for a change of the data: its `done` carries the next version. */
const DATA_REQUEST = 'read score as a share';
const PREPARED = {
  ...DATASET,
  preview: [
    ['1.5', '0.52'],
    ['2.0', '0.58'],
  ],
  changes: ['score: 2 cells divided by 100'],
  version: 2,
  can_undo: true,
};

/**
 * The spec's roles as the open names them for the start item's chips: a role of two kinds, a
 * family and an optional role of categories.
 */
const OPEN_ROLES = [
  { name: 'x', kinds: ['numeric', 'datetime'], required: true, variadic: false, description: 'x' },
  { name: 'y', kinds: ['numeric'], required: true, variadic: true, description: 'the series' },
  {
    name: 'series',
    kinds: ['categorical'],
    required: false,
    variadic: false,
    description: 'one colour per group',
  },
];

/** How the session's open answers, the same on both lanes. */
type Open = 'ok' | 'hold' | 'error' | 'ineligible' | 'not_enabled';
let open: Open;
/** The open names the spec's roles (`OPEN_ROLES`); without, the start item has no chips. */
let roles: boolean;
/** The public lane's door (`GET /agent/lane`). */
let door: boolean;
/** The service spent its day budget: `/status` says `paused` until the next day. */
let paused: boolean;
/** The message whose turn finds the session gone (`404 session_expired`). */
const EXPIRING = 'are you still there?';
/** The parse binds `x` only: `y` misses a column, and the card's dropdowns open by themselves. */
let missingY: boolean;
/** The plots the session made so far: each plot turn ships the next version. */
let plots: number;

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
        // With previews, so the start item shows the catalogue plot's thumbnail.
        return json(200, {
          title: 'Basic Scatter Plot',
          data: ['`x` (numeric) - the horizontal axis', '`y` (numeric) - the vertical axis'],
          implementations: ['matplotlib', 'seaborn'].map(library_id => ({
            library_id,
            preview_url: `https://img.test/scatter-basic/${library_id}/plot.png`,
            preview_url_light: `https://img.test/scatter-basic/${library_id}/plot-light.png`,
            preview_url_dark: `https://img.test/scatter-basic/${library_id}/plot-dark.png`,
          })),
        });
      }
      if (path === '/debug/agent/status' || path === '/agent/status') {
        return json(200, {
          libraries: ['matplotlib', 'seaborn'],
          enabled: true,
          user_max_runs: 2,
          ...(paused ? { paused: true, resets_at: '2999-01-01T00:00:00Z' } : {}),
        });
      }
      if ((path === '/debug/agent/sessions' || path === '/agent/sessions') && method === 'POST') {
        if (open === 'hold') return new Promise<Response>(() => undefined);
        if (open === 'error') return json(500, { detail: 'internal', ref: 'r-500' });
        if (open === 'ineligible') return json(422, { detail: 'not_eligible', ref: 'r-ne' });
        // The kill switch: the admin menu holds a line of its own about it, the page none.
        if (open === 'not_enabled') return json(404, { detail: 'not_enabled', ref: 'r-off' });
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
          ...(roles ? { roles: OPEN_ROLES } : {}),
        });
      }
      const rest = path.match(/^\/debug\/agent\/sessions\/S1(\/.*)?$|^\/agent\/session(\/.*)?$/);
      if (!rest) return json(404, { detail: 'not_found' });
      const sub = rest[1] ?? rest[2] ?? '';
      if (method === 'DELETE' && sub === '') return new Response(null, { status: 204 });
      if (sub === '/dataset' && method === 'POST') {
        return json(
          200,
          missingY ? { ...DATASET, bindings: [{ role: 'x', column: 'hours' }] } : DATASET
        );
      }
      if (sub === '/bindings' && method === 'PUT') {
        const bindings = JSON.parse(String(init.body)) as { role: string }[];
        const missing = ['x', 'y'].filter(role => !bindings.some(bound => bound.role === role));
        return json(200, { bindings, complete: missing.length === 0, missing_roles: missing });
      }
      if (sub === '/dataset/confirm') return json(200, { confirmed: true, rows: 2, columns: 2 });
      if (sub === '/dataset/undo' && method === 'POST') return json(200, DATASET);
      // The library menu's switch: the plot there may take the two decisions along.
      if (sub === '/library' && method === 'POST') {
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
          target: { spec_id: 'scatter-basic', library: 'seaborn' },
          carry: { decisions: 2, newer: 2, target_has_plot: false, from_plot: true, offer: true },
        });
      }
      if (sub === '/messages') {
        const body = JSON.parse(String(init.body)) as { action?: string; text?: string };
        if (body.text === EXPIRING) return json(404, { detail: 'session_expired', ref: 'r-gone' });
        if (body.action === 'summarize_data') {
          return sse([
            ['message', { text: SUMMARY }],
            ['done', { llm_calls: 1 }],
          ]);
        }
        if (body.text === DATA_REQUEST) {
          return sse([
            ['message', { text: 'Score is a share now.' }],
            [
              'done',
              {
                llm_calls: 2,
                bindings: PREPARED.bindings,
                data_confirmed: false,
                dataset: PREPARED,
              },
            ],
          ]);
        }
        plots += 1;
        return sse([
          ['plot', { ...PLOT, version: plots }],
          ['message', { text: plots === 1 ? 'Here is your plot.' : `Plot ${plots}.` }],
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

/** Send a message from the box with Enter, and wait until its reply is in and its turn ended. */
async function send(text: string, reply: string) {
  const box = screen.getByLabelText('Message');
  fireEvent.change(box, { target: { value: text } });
  fireEvent.keyDown(box, { key: 'Enter' });
  expect(await screen.findByText(reply)).toBeInTheDocument();
  await turnEnded();
}

/** Who looks: a visitor, an admin on the admin lane, an admin in "view as visitor". */
type Who = 'visitor' | 'admin' | 'as visitor';

interface State {
  open: Open;
  reach: () => Promise<void>;
  /** The open names the spec's roles; not unless said. */
  roles?: boolean;
  /** The parse leaves `y` without a column; not unless said. */
  missingY?: boolean;
  /** The public door; open unless said. */
  door?: boolean;
  /** The service's day budget is spent. */
  paused?: boolean;
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
  // The start item with its chips, the thumbnail and both ⓘ.
  'ready with the spec roles': {
    open: 'ok',
    roles: true,
    reach: async () => {
      await waitFor(() => expect(screen.getByLabelText('Message')).toBeEnabled());
      await screen.findByRole('list', { name: 'What the plot needs' });
      await screen.findByRole('button', { name: 'Show the matplotlib catalogue plot large' });
    },
  },
  // The start item's thumbnail opened large, in its dialog.
  'with the catalogue plot open': {
    open: 'ok',
    roles: true,
    reach: async () => {
      await waitFor(() => expect(screen.getByLabelText('Message')).toBeEnabled());
      fireEvent.click(
        await screen.findByRole('button', { name: 'Show the matplotlib catalogue plot large' })
      );
      await screen.findByRole('dialog', { name: '# Basic Scatter Plot · matplotlib' });
    },
  },
  // The start item's columns ⓘ open, in its popover.
  'with the columns ⓘ open': {
    open: 'ok',
    roles: true,
    reach: async () => {
      await waitFor(() => expect(screen.getByLabelText('Message')).toBeEnabled());
      fireEvent.click(await screen.findByRole('button', { name: 'Columns the plot expects' }));
      await screen.findByRole('dialog', { name: 'Columns the plot expects' });
    },
  },
  'with data': { open: 'ok', reach: pasteTable },
  // The start item stays first, above the paste, its chips and its thumbnail.
  'with data after the spec roles': { open: 'ok', roles: true, reach: pasteTable },
  // The card's dropdowns, opened with `.change()` on its bindings line.
  'with the bindings open': {
    open: 'ok',
    reach: async () => {
      await pasteTable();
      fireEvent.click(screen.getByRole('button', { name: 'Change the bindings' }));
      await screen.findByTestId('bindings-editor');
    },
  },
  // A required role without a column: the dropdowns open by themselves.
  'with a missing role': {
    open: 'ok',
    missingY: true,
    reach: async () => {
      await pasteTable();
      await screen.findByText('* required: pick a column for y');
    },
  },
  'with a plot': { open: 'ok', reach: plotOnce },
  // A second version: the first folds to its label, `▸ plot v1 · matplotlib · first plot`.
  'with two plots, the older folded': {
    open: 'ok',
    reach: async () => {
      await plotOnce();
      fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });
      const update = screen.getByRole('button', { name: 'Update plot' });
      await waitFor(() => expect(update).not.toHaveAttribute('aria-disabled'));
      fireEvent.click(update);
      expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
      await turnEnded();
      await screen.findByRole('button', { name: 'Plot v1, matplotlib, first plot' });
    },
  },
  // The chapters after a data request below the plot: the card in a new `# data` chapter at the
  // end, the version before folded where the card stood, and opened read-only.
  'with a folded data version open': {
    open: 'ok',
    reach: async () => {
      await plotOnce();
      await send(DATA_REQUEST, 'Score is a share now.');
      fireEvent.click(
        await screen.findByRole('button', { name: 'Data v1, pasted, 2 rows by 2 columns' })
      );
      await screen.findByTestId('folded-data-source');
    },
  },
  // `.undo()` on the card above the plot: its version moves the card to the end as a new data
  // chapter, and the focus follows it.
  'with a control version after a plot': {
    open: 'ok',
    reach: async () => {
      await pasteTable();
      await send(DATA_REQUEST, 'Score is a share now.');
      const create = screen.getByRole('button', { name: 'Create plot' });
      await waitFor(() => expect(create).not.toHaveAttribute('aria-disabled'));
      fireEvent.click(create);
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      await turnEnded();
      const undo = screen.getByRole('button', { name: '.undo()' });
      undo.focus();
      fireEvent.click(undo);
      await screen.findByText('# undone · back to the version before');
      await waitFor(() => expect(screen.getByTestId('data-card-label')).toHaveFocus());
    },
  },
  // Before any plot, the same rule: a data request puts the card before its reply, and `.undo()`
  // then moves it to the end, each earlier version folded under its own talk.
  'with a control version before any plot': {
    open: 'ok',
    reach: async () => {
      await pasteTable();
      await send(DATA_REQUEST, 'Score is a share now.');
      const undo = screen.getByRole('button', { name: '.undo()' });
      undo.focus();
      fireEvent.click(undo);
      await screen.findByText('# undone · back to the version before');
      await waitFor(() => expect(screen.getByTestId('data-card-label')).toHaveFocus());
      expect(screen.getAllByTestId('data-stub')).toHaveLength(2);
    },
  },
  // A library switch after a plot: a line of its own, which names the decisions the plot there
  // keeps.
  'with a library switch line': {
    open: 'ok',
    reach: async () => {
      await plotOnce();
      fireEvent.click(screen.getByTestId('library-chip'));
      const menu = await screen.findByRole('dialog', { name: 'Library of the plot' });
      const seaborn = await within(menu).findByRole('button', { name: 'seaborn' });
      await waitFor(() => expect(seaborn).toBeEnabled());
      fireEvent.click(seaborn);
      expect(await screen.findByTestId('switch-line')).toHaveTextContent(
        '· plotting in seaborn from here, 2 decisions kept'
      );
    },
  },
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
  // The kill switch: the same words for both; the admin's diagnostics line is the menu's.
  'switched off (not_enabled)': {
    open: 'not_enabled',
    reach: async () => {
      await screen.findByText(/^error · not_enabled/);
    },
  },
  // The day budget spent: the pause note above the composer, from the lane's own `/status`.
  paused: {
    open: 'ok',
    paused: true,
    reach: async () => {
      await waitFor(() => expect(screen.getByLabelText('Message')).toBeEnabled());
      await screen.findByText(/paused/);
    },
  },
  // A turn that finds the session gone: the error in the thread, with its reload.
  'session expired': {
    open: 'ok',
    reach: async () => {
      const box = await screen.findByLabelText('Message');
      await waitFor(() => expect(box).toBeEnabled());
      fireEvent.change(box, { target: { value: EXPIRING } });
      fireEvent.keyDown(box, { key: 'Enter' });
      await screen.findByRole('button', { name: 'reload' });
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
  // A table waiting in the box: the plot button inert, the status line saying Enter reads it.
  'with a table attached': {
    open: 'ok',
    reach: async () => {
      const box = await screen.findByLabelText('Message');
      await waitFor(() => expect(box).toBeEnabled());
      fireEvent.paste(box, {
        clipboardData: { files: [], getData: () => 'hours,score\n1.5,52\n2.0,58\n' },
      });
      await screen.findByRole('group', { name: /^Attached/ });
    },
  },
  // Text in the box after a plot: `.update_plot() →` acts, `.start_over()` at the line's end.
  'with a change typed after a plot': {
    open: 'ok',
    reach: async () => {
      await plotOnce();
      fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });
      await waitFor(() =>
        expect(screen.getByRole('button', { name: 'Update plot' })).not.toHaveAttribute(
          'aria-disabled'
        )
      );
    },
  },
  // The chat's own feedback before a plot, opened from `.feedback()` at the status line's end.
  'with the chat feedback form open': {
    open: 'ok',
    reach: async () => {
      await pasteTable();
      fireEvent.click(screen.getByRole('button', { name: 'Give feedback on this chat' }));
      await screen.findByRole('form', { name: 'Feedback on this chat' });
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
/**
 * The admin menu's elements, by name: the prefix above leaves out exactly these, each once, so
 * a new element that the prefix would exempt has to be added here on purpose.
 */
const ADMIN_ONLY_IDS = ['admin-menu', 'admin-menu-panel', 'admin-menu-row'] as const;
/** The test ids the last snapshot left out. */
let leftOut: string[] = [];

/** The page's DOM without the admin-only elements, React's ids numbered by first appearance. */
function snapshot(): string {
  const body = document.body.cloneNode(true) as HTMLElement;
  const exempt = [...body.querySelectorAll(ADMIN_ONLY)];
  leftOut = exempt.map(element => element.getAttribute('data-testid') ?? '');
  for (const element of exempt) element.remove();
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
  roles = STATES[state].roles ?? false;
  door = STATES[state].door ?? true;
  paused = STATES[state].paused ?? false;
  missingY = STATES[state].missingY ?? false;
  plots = 0;
  stubFetch();
  renderPage();
  await STATES[state].reach();
  const dom = await settled();
  // Exactly the admin menu's elements were left out, each once: its button and popover, and
  // its row on the closed door's page; a visitor's page has none.
  const expected =
    who === 'visitor' ? [] : door ? ['admin-menu', 'admin-menu-panel'] : [...ADMIN_ONLY_IDS];
  expect(
    leftOut.every(id => (ADMIN_ONLY_IDS as readonly string[]).includes(id)),
    leftOut.join()
  ).toBe(true);
  expect([...leftOut].sort(), `${who} left out`).toEqual([...expected].sort());
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
    // The fan-out is off: the only other allowed difference does not apply here. The chip names
    // one library, the one the session switched to included, never `all`.
    if (door) {
      expect(screen.getByTestId('library-chip')).toHaveTextContent(/^(matplotlib|seaborn) ▾$/);
    }
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
