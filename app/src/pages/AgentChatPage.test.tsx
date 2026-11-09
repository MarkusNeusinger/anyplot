import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { analyticsMuted } from 'src/analytics/mute';
import type { MemoryEntry } from 'src/lib/agent';
import { AgentChatPage } from 'src/pages/AgentChatPage';
import { LEAVE_TEXT, localClock, nextUtcMidnight } from 'src/sections/agent-chat/messages';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY, VIEW_AS_VISITOR_KEY } from 'src/utils/adminAuth';

const flags = vi.hoisted(() => ({ agentChat: true, isDev: false }));

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    CONFIG: {
      ...actual.CONFIG,
      get isDev() {
        return flags.isDev;
      },
      features: {
        get agentChat() {
          return flags.agentChat;
        },
      },
    },
  };
});

// Stable identities, like the real hook (effects depend on them).
const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

let fetchMock: ReturnType<typeof vi.fn>;
/**
 * The admin lane's `GET /status`, the page's admin check: 200, a refusal (401, 403), `404
 * not_enabled` (the gate let it through, the kill switch is off), or no answer at all.
 */
let adminStatus: 200 | 401 | 403 | 404 | 'unreachable' = 200;

/** The spec's `## Data` bullets as the catalogue API serves them: two columns and two meta lines. */
const SPEC_DATA = [
  '`x` (numeric) - Independent variable values plotted on the horizontal axis',
  '`y` (numeric) - Dependent variable values plotted on the vertical axis',
  'Size: 50-500 points recommended for clear visualization',
  'Example: Random correlated data with moderate positive correlation',
];
/** A catalogue implementation with its themed previews. */
const catalogueImpl = (library_id: string) => ({
  library_id,
  preview_url_light: `https://img.test/scatter-basic/${library_id}/plot-light.png`,
  preview_url_dark: `https://img.test/scatter-basic/${library_id}/plot-dark.png`,
});
/** Answers a parse held back with `slow` in its text; set while it is pending. */
let releaseParse: (() => void) | null = null;
/** Set to hold the next turn's stream back until `releaseTurn` answers it. */
let holdNextTurn = false;
let releaseTurn: (() => void) | null = null;

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

/** `done.dataset`: the assistant read `score` anew, as the next version. */
const PREPARED = {
  preview: [
    ['1.5', '0.52'],
    ['2.0', '0.58'],
  ],
  profile: {
    ...DATASET.profile,
    columns: [
      { name: 'hours', dtype: 'number', missing: 0, unique: 2 },
      { name: 'score', dtype: 'number', missing: 0, unique: 2 },
    ],
  },
  bindings: DATASET.bindings,
  warnings: [],
  changes: ["score: 2 cells read as numbers, unit '%' removed"],
  version: 2,
};

/** `done.dataset` after `generate_data` in a session without data: version 1, with the roles. */
const GENERATED = {
  preview: [
    ['-3.1415927', '-1.2246468e-16'],
    ['3.1415927', '1.2246468e-16'],
  ],
  profile: {
    rows: 200,
    columns: [
      { name: 'x', dtype: 'number', missing: 0, unique: 200 },
      { name: 'y', dtype: 'number', missing: 0, unique: 199 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  bindings: [
    { role: 'x', column: 'x' },
    { role: 'y', column: 'y' },
  ],
  warnings: [],
  roles: DATASET.roles,
  changes: ['generated 200 rows: x from -3.1416 to 3.1416, y = sin(x)'],
  version: 1,
};

/**
 * The stub server's numbering, as the agents service numbers its versions: every stored
 * version takes the session's next number, never one twice, and an undo brings the version
 * before back under its own (every undo here goes back to the data's first version).
 */
let lastVersion = 0;
let dataFirst = 1;
/** A stored paste: new data, its first version. */
function pasted() {
  lastVersion += 1;
  dataFirst = lastVersion;
  return { ...DATASET, version: lastVersion, can_undo: false, original_version: dataFirst };
}
/** A version a turn made from the data: on top of it, with the one before to undo. */
function changedVersion<T extends object>(dataset: T) {
  lastVersion += 1;
  return { ...dataset, version: lastVersion, can_undo: true, original_version: dataFirst };
}
/** A table a turn computed in a session without data: the session's next number, new data. */
function generatedVersion<T extends object>(dataset: T) {
  lastVersion += 1;
  dataFirst = lastVersion;
  return { ...dataset, version: lastVersion, can_undo: false, original_version: dataFirst };
}
/** `.undo()`: the data's first version again, with nothing before it. */
function undone() {
  return { ...DATASET, version: dataFirst, can_undo: false, original_version: dataFirst };
}

const FORMULA = 'y = sin(x), x von -pi bis pi';
const EXAMPLE_REPLY = 'I generated example data to try the plot: 200 rows of x and y, all made up.';

/** Free text the server reads into a table with a model and does not store. */
/** Free text the stub reads as a table to decide on: three rows, so the message box attaches it. */
const FREE_TEXT = 'Hund 7, Katze 3\nVogel 4, Maus 2\nPferd 1, Esel 5';
const TRANSCRIBED = {
  transcribed: true,
  text: 'animal,count\nHund,7\nKatze,3\nVogel,4\n',
  preview: [
    ['Hund', '7'],
    ['Katze', '3'],
    ['Vogel', '4'],
  ],
  profile: {
    rows: 3,
    columns: [
      { name: 'animal', dtype: 'text', missing: 0, unique: 3 },
      { name: 'count', dtype: 'integer', missing: 0, unique: 3 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  warnings: [],
  note: '',
};

const SUMMARY = '2 rows: hours and score, both numbers. Is hours the x axis?';

/** A shipped first plot; its artifacts are not served here, which the card shows as failed. */
const PLOT = {
  status: 'ok',
  attempts: 1,
  artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
  changes: [],
  residual_defects: [],
  version: 1,
};

/** A turn's stream as the BFF sends it. */
function sse(events: [string, unknown][]) {
  return new Response(
    events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join(''),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
  );
}

function turnEvents(body: { text?: string; action?: string }): [string, unknown][] {
  // After every stored parse the page asks for the step-1 summary.
  if (body.action === 'summarize_data') {
    return [
      ['message', { text: SUMMARY }],
      ['done', { llm_calls: 1 }],
    ];
  }
  // The first plot: `.create_plot()` as it is, or with a change the user typed first; `plot the
  // new data` the same way.
  if (
    body.action === 'create_plot' ||
    body.action === 'plot_new_data' ||
    body.text?.includes('log scale')
  ) {
    return [
      ['plot', PLOT],
      ['message', { text: 'Here is your plot.' }],
      ['done', { llm_calls: 2, data_confirmed: true }],
    ];
  }
  // A question the assistant answers without touching the data or the bindings.
  if (body.text?.includes('mean')) {
    return [
      ['message', { text: 'The mean score is 55.' }],
      ['done', { llm_calls: 1 }],
    ];
  }
  // A question about the data: the server reports the confirmation it holds, which a
  // table read from text and then discarded left in place.
  if (body.text?.includes('columns')) {
    return [
      ['message', { text: 'Two columns: hours and score.' }],
      ['done', { llm_calls: 1, data_confirmed: true }],
    ];
  }
  // `.example_data()`: the assistant's `run_data_code` made example data, the first data.
  if (body.action === 'example_data') {
    return [
      ['message', { text: EXAMPLE_REPLY }],
      [
        'done',
        {
          llm_calls: 3,
          bindings: GENERATED.bindings,
          data_confirmed: false,
          dataset: generatedVersion({
            ...GENERATED,
            changes: ['generated example data: 200 rows, 2 columns'],
          }),
        },
      ],
    ];
  }
  // The assistant's `generate_data` computed the first data from a formula.
  if (body.text?.includes('sin(')) {
    return [
      ['message', { text: 'I generated 200 rows from y = sin(x).' }],
      [
        'done',
        {
          llm_calls: 2,
          bindings: GENERATED.bindings,
          data_confirmed: false,
          dataset: generatedVersion(GENERATED),
        },
      ],
    ];
  }
  // The assistant's `prepare_data` changed the data; `done` carries the new version.
  if (body.text?.includes('prozent')) {
    return [
      ['message', { text: 'I read score as numbers.' }],
      [
        'done',
        {
          llm_calls: 2,
          bindings: PREPARED.bindings,
          data_confirmed: false,
          dataset: changedVersion(PREPARED),
        },
      ],
    ];
  }
  // The root swapped the columns during the turn; `done` syncs the result.
  return [
    ['message', { text: 'Swapped.' }],
    [
      'done',
      {
        llm_calls: 2,
        bindings: [
          { role: 'x', column: 'score' },
          { role: 'y', column: 'hours' },
        ],
        data_confirmed: false,
      },
    ],
  ];
}

function stubFetch(
  openStatus = 200,
  openBody: unknown = { status: openStatus, message: 'admin required' }
) {
  fetchMock = vi.fn(async (input: string, init: RequestInit = {}) => {
    const url = new URL(input);
    const method = init.method ?? 'GET';
    if (url.pathname.endsWith('/debug/agent/sessions') && method === 'POST') {
      return openStatus === 200
        ? json(200, {
            session_id: 'S1',
            eligibility: { eligible: true, status: 'clean', reasons: [] },
          })
        : json(openStatus, openBody);
    }
    if (url.pathname.endsWith('/debug/agent/status')) {
      if (adminStatus === 'unreachable') throw new TypeError('Failed to fetch');
      if (adminStatus === 404) return json(404, { detail: 'not_enabled' });
      if (adminStatus !== 200) return json(adminStatus, { detail: 'Invalid admin token' });
      return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true });
    }
    if (url.pathname.endsWith('/sessions/S1/dataset') && method === 'POST') {
      const text = String(init.body);
      // A formula is refused: the chat computes it.
      if (text.includes('sin(')) return json(422, { detail: 'formula', ref: 'r-f' });
      if (text.includes('Hund')) return json(200, TRANSCRIBED);
      if (text.includes('slow')) {
        return new Promise<Response>(resolve => {
          releaseParse = () => resolve(json(200, pasted()));
        });
      }
      return json(200, pasted());
    }
    if (url.pathname.endsWith('/sessions/S1/bindings') && method === 'PUT') {
      return json(200, {
        bindings: JSON.parse(String(init.body)),
        complete: true,
        missing_roles: [],
      });
    }
    if (url.pathname.endsWith('/sessions/S1/dataset/confirm') && method === 'POST') {
      return json(200, { confirmed: true, rows: 2, columns: 2 });
    }
    if (url.pathname.endsWith('/sessions/S1/dataset/undo') && method === 'POST') {
      return json(200, undone());
    }
    if (url.pathname.endsWith('/sessions/S1/messages') && method === 'POST') {
      const response = sse(turnEvents(JSON.parse(String(init.body))));
      if (!holdNextTurn) return response;
      holdNextTurn = false;
      return new Promise<Response>(resolve => {
        releaseTurn = () => resolve(response);
      });
    }
    if (url.pathname.endsWith('/specs/scatter-basic')) {
      return json(200, {
        title: 'Basic Scatter Plot',
        data: SPEC_DATA,
        implementations: ['matplotlib', 'seaborn'].map(catalogueImpl),
      });
    }
    if (method === 'DELETE') return new Response(null, { status: 204 });
    return json(404, { detail: 'not_found' });
  });
  vi.stubGlobal('fetch', fetchMock);
}

function LocationProbe() {
  const current = useLocation();
  return <output data-testid="location">{`${current.pathname}${current.search}`}</output>;
}

/** A data router, as in the app: the page's leave warning uses the router's blocker. */
function renderAt(url: string) {
  const router = createMemoryRouter(
    [
      {
        path: '/agent',
        element: (
          <>
            <AgentChatPage />
            <LocationProbe />
          </>
        ),
      },
      { path: '*', element: <LocationProbe /> },
    ],
    { initialEntries: [url] }
  );
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

const PAGE = '/agent?spec=scatter-basic&library=matplotlib&language=python';
/**
 * The calls to the admin lane's BFF. The flows below run for an admin (the hint, or local
 * development), on the admin lane; a visitor's page is AgentChatPage.public.test.tsx, and the
 * two lanes' DOM is compared in AgentChatPage.parity.test.tsx.
 */
const agentCalls = () =>
  fetchMock.mock.calls.filter(([input]) => String(input).includes('/debug/agent'));
/** The path of a call, without the query (a turn carries the site theme there). */
const pathOf = (input: unknown) => new URL(String(input)).pathname;
/** The bodies of the chat turns the page posted, in order. */
const turnBodies = () =>
  agentCalls()
    .filter(([input]) => pathOf(input).endsWith('/messages'))
    .map(([, init]) => JSON.parse(String((init as RequestInit).body)) as Record<string, string>);
const lastTurn = () => turnBodies().slice(-1)[0];

/** The turn in flight is over: its `done` was applied and `.stop()` gave way. */
const turnEnded = () =>
  waitFor(() => expect(screen.queryByRole('button', { name: 'Stop' })).not.toBeInTheDocument());

/**
 * Paste `value` into the message box, where a table becomes the attachment, and send it with
 * Enter, with `note` typed beside it. Text that routes as a message would stay in the box: the
 * tests paste tables.
 */
async function attachAndSend(value: string, note = '') {
  const box = await screen.findByLabelText('Message');
  await waitFor(() => expect(box).toBeEnabled());
  fireEvent.paste(box, { clipboardData: { files: [], getData: () => value } });
  await screen.findByRole('group', { name: /^Attached/ });
  if (note) fireEvent.change(box, { target: { value: note } });
  fireEvent.keyDown(box, { key: 'Enter' });
}

/** Paste a table and wait for its summary: step 1 with data, nothing in flight. */
async function parseAndSummarize(value = 'hours,score\n1.5,52\n2.0,58\n') {
  await attachAndSend(value);
  expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
  await turnEnded();
}

/** Paste a table, then one `.create_plot()`: the data is confirmed and the first plot ships. */
async function parseAndPlot(value?: string) {
  await parseAndSummarize(value);
  const create = screen.getByRole('button', { name: 'Create plot' });
  await waitFor(() => expect(create).not.toHaveAttribute('aria-disabled'));
  fireEvent.click(create);
  expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
  await turnEnded();
}

/** The paths of the session's calls to the confirm route and the turns, in order. */
const confirmAndTurns = () =>
  agentCalls()
    .map(([input, init]) => {
      const path = pathOf(input);
      if (path.endsWith('/dataset/confirm')) return 'confirm';
      if (!path.endsWith('/messages')) return null;
      const body = JSON.parse(String((init as RequestInit).body)) as Record<string, string>;
      return body.action ?? `text: ${body.text}`;
    })
    .filter(Boolean);

/** Send `text` from the composer with Enter. */
function sendFromComposer(text: string) {
  const box = screen.getByLabelText('Message');
  fireEvent.change(box, { target: { value: text } });
  fireEvent.keyDown(box, { key: 'Enter' });
}

/** In step 2, paste free text into the message box, which comes back as a table to decide on. */
async function transcribeInStep2() {
  await attachAndSend(FREE_TEXT);
  await screen.findByTestId('transcription-card');
}

/**
 * The composer's controls in their fixed order, as each reads now: the data line's
 * `.example_data()`, then the row's buttons. `.open()`, which stands in every state, is left out,
 * and an inert one (`aria-disabled`, so it keeps the focus) ends in ` (inert)`. The `↵` in the box
 * shows on a touch screen only, so it is hidden here.
 */
const composerButtons = () =>
  [
    ...within(screen.getByTestId('data-line')).queryAllByRole('button'),
    ...within(screen.getByLabelText('Message').closest('form') as HTMLElement).queryAllByRole(
      'button'
    ),
  ]
    .filter(button => button.textContent !== '.open()')
    .map(
      button =>
        `${button.textContent}${button.getAttribute('aria-disabled') === 'true' ? ' (inert)' : ''}`
    );

/** The actions at the end of the status line at the frame's foot, as they read. */
const statusActions = () => {
  const actions = screen.queryByTestId('status-actions');
  return actions
    ? within(actions)
        .getAllByRole('button')
        .map(button => button.textContent)
    : [];
};

/** Wait until a composer button acts: an inert one is `aria-disabled`, never `disabled`. */
const untilActive = (button: HTMLElement) =>
  waitFor(() => expect(button).not.toHaveAttribute('aria-disabled'));

/** The thread's last entry. */
const lastInThread = () => screen.getByRole('log', { name: 'Conversation' }).lastElementChild;

/**
 * A thread line that repeats a lost confirmation the step line above the composer names, in the
 * words the notices had ("bindings changed · check them, then …", "check the data again, …"):
 * there is none since 2026-11-06.
 */
const lossNotice = () =>
  within(screen.getByRole('log', { name: 'Conversation' })).queryByText(
    /changed · check (it|them), then|check the data again/
  );

/** The thread's latest bubble of a page turn: the button the user pressed. */
const lastAction = () => {
  const bubbles = within(screen.getByRole('log', { name: 'Conversation' })).getAllByTestId(
    'action-item'
  );
  return bubbles[bubbles.length - 1];
};

/** `.change()` on the data card's bindings line: the dropdowns open. */
const openBindings = () =>
  fireEvent.click(screen.getByRole('button', { name: 'Change the bindings' }));

/** The data card's bindings line (`x (across): hours · y (up): score`). */
const bindingsLine = () => screen.getByTestId('bindings-line');

/** The thread's chapters in order, by their line (`# data`, `# plot`). */
const chapters = () =>
  screen.queryAllByTestId('chapter-line').map(line => line.getAttribute('data-chapter'));

/** The labels of the folded data versions, in thread order (`▸ data v1 · pasted · …`). */
const foldedData = () =>
  screen.queryAllByTestId('data-stub-label').map(label => label.textContent?.replace(/^▸/, ''));

/** Whether the live data card is the thread's last entry, in the `# data` chapter that ends it. */
const cardAtTheEnd = () => {
  const card = screen.getByTestId('data-card');
  const lines = screen.getAllByTestId('chapter-line');
  const chapter = lines[lines.length - 1];
  return (
    screen.getByRole('log', { name: 'Conversation' }).lastElementChild === card &&
    chapter.getAttribute('data-chapter') === 'data' &&
    !!(chapter.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING)
  );
};

/** The step the status line at the frame's foot names (`step 1 of 2 · …`). */
const currentStep = () => {
  const line = screen.getByTestId('data-step');
  const step = Number(line.getAttribute('data-step'));
  expect(line).toHaveTextContent(new RegExp(`^>>> (back to )?step ${step} of 2 · `));
  return step;
};

/** The header's library menu: its chip, which names the library (or `all`). */
const libraryChip = () => screen.getByTestId('library-chip');
const MENU = { name: 'Library of the plot' } as const;

/**
 * Open the library menu, as a click does (the chip takes the focus first, so the
 * popover returns it there); the page behind it is hidden from the queries meanwhile.
 */
async function openLibraryMenu() {
  await waitFor(() => expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument());
  const chip = libraryChip();
  await waitFor(() => expect(chip).toBeEnabled());
  chip.focus();
  fireEvent.click(chip);
  return screen.findByRole('dialog', MENU);
}

/** Close the open library menu with Escape, and wait until the page is back. */
async function closeLibraryMenu() {
  fireEvent.keyDown(screen.getByRole('dialog', MENU), { key: 'Escape' });
  await waitFor(() => expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument());
}

const ADMIN_MENU = { name: 'Admin' } as const;
/** The admin menu's fan-out toggle (`all 2 libraries`), in the open menu. */
const ALL_TOGGLE = { name: /^all \d+ libraries$/ } as const;

/** Open the admin menu, the page's one admin-only element. */
async function openAdminMenu() {
  await waitFor(() => expect(screen.queryByRole('dialog', ADMIN_MENU)).not.toBeInTheDocument());
  const button = await screen.findByTestId('admin-menu');
  button.focus();
  fireEvent.click(button);
  return screen.findByRole('dialog', ADMIN_MENU);
}

/** Close the open admin menu with Escape, and wait until the page is back. */
async function closeAdminMenu() {
  fireEvent.keyDown(screen.getByRole('dialog', ADMIN_MENU), { key: 'Escape' });
  await waitFor(() => expect(screen.queryByRole('dialog', ADMIN_MENU)).not.toBeInTheDocument());
}

/** Turn the admin menu's fan-out on or off (`all N libraries`), and wait until the menu closed. */
async function toggleAll() {
  const menu = await openAdminMenu();
  const toggle = await within(menu).findByRole('button', ALL_TOGGLE);
  await waitFor(() => expect(toggle).toBeEnabled());
  fireEvent.click(toggle);
  await waitFor(() => expect(screen.queryByRole('dialog', ADMIN_MENU)).not.toBeInTheDocument());
}

/** Pick the library `name` in the library menu, and wait until it closed. */
async function pickInMenu(name: string) {
  const menu = await openLibraryMenu();
  const option = await within(menu).findByRole('button', { name });
  await waitFor(() => expect(option).toBeEnabled());
  fireEvent.click(option);
  await waitFor(() => expect(screen.queryByRole('dialog', MENU)).not.toBeInTheDocument());
}

beforeEach(() => {
  flags.agentChat = true;
  flags.isDev = false;
  localStorage.clear();
  sessionStorage.clear();
  adminStatus = 200;
  releaseParse = null;
  holdNextTurn = false;
  releaseTurn = null;
  lastVersion = 0;
  dataFirst = 1;
  analytics.trackEvent.mockClear();
  analytics.trackPageview.mockClear();
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('AgentChatPage gating', () => {
  it('is the 404 page when the build has no agent chat', () => {
    flags.agentChat = false;
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    expect(screen.getByLabelText('Page not found')).toBeInTheDocument();
    expect(agentCalls()).toHaveLength(0);
  });

  it('treats a browser without the admin hint as a visitor: no call to the debug API', async () => {
    // The public door is closed in this file (the build flag of `useAgentLaneOpen` is off).
    renderAt(PAGE);
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    expect(screen.queryByTestId('admin-menu')).not.toBeInTheDocument();
    expect(agentCalls()).toHaveLength(0);
  });

  it('checks the admin first, then opens the session on the admin lane and records nothing', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&source=plot_page`);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open a data file' })).toBeInTheDocument();
    // The admin check picks the lane, so it goes before the session's open.
    const called = agentCalls().map(([input]) => pathOf(input));
    expect(called[0]).toBe('/debug/agent/status');
    expect(called.indexOf('/debug/agent/sessions')).toBeGreaterThan(0);
    // Once: the chat takes the check's answer for its libraries, its run cap and the pause.
    expect(called.filter(path => path === '/debug/agent/status')).toHaveLength(1);
    // The one admin-only element, at the header row's end.
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin ▾$/);
    // The admin's own use is no visitor's: no pageview and no `agent_open`; the source still goes.
    expect(analytics.trackPageview).not.toHaveBeenCalled();
    expect(analytics.trackEvent).not.toHaveBeenCalledWith('agent_open', expect.anything());
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(PAGE));
    // The title in plain words is the link back, in the frame's header row (`← title` until v4).
    const back = await screen.findByRole('link', { name: 'Basic Scatter Plot' });
    expect(back).toHaveAttribute('href', expect.stringContaining('scatter-basic'));
    expect(screen.getByRole('region', { name: 'Chat' })).toContainElement(back);
    expect(screen.getByTestId('chat-frame-tab')).toHaveTextContent(/^~\/anyplot\.ai\/agent$/);
  });

  it("mutes the site's analytics while it serves an admin, and only until it unmounts", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const view = renderAt(PAGE);
    // The check is out, and already the admin's: nothing the page or its parts send counts.
    expect(analyticsMuted()).toBe(true);
    await screen.findByLabelText('Message');
    expect(analyticsMuted()).toBe(true);
    // The next page records its own pageview again.
    view.unmount();
    expect(analyticsMuted()).toBe(false);

    // A visitor's browser is never muted.
    localStorage.clear();
    renderAt(PAGE);
    await screen.findByText(/the assistant is closed right now/);
    expect(analyticsMuted()).toBe(false);
  });

  it('names the tab after the spec title, not its id', async () => {
    flags.isDev = true;
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    await waitFor(() => expect(document.title).toBe('agent · Basic Scatter Plot | anyplot.ai'));
  });

  it('lets local development in on the admin lane without the hint', async () => {
    flags.isDev = true;
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(agentCalls().map(([input]) => pathOf(input))).toContain('/debug/agent/sessions');
    expect(screen.getByTestId('admin-menu')).toBeInTheDocument();
  });

  it('explains the missing parameters instead of opening a session', async () => {
    flags.isDev = true;
    renderAt('/agent?spec=scatter-basic&library=excel');
    // The plot page's entry since 2026-11-02 is `.use_my_data()`.
    expect(await screen.findByText(/open it from a plot/)).toHaveTextContent(
      "open it from a plot's .use_my_data(), or start with scatter-basic in matplotlib."
    );
    expect(screen.getByRole('link', { name: 'scatter-basic in matplotlib' })).toHaveAttribute(
      'href',
      '/agent?spec=scatter-basic&library=matplotlib&language=python'
    );
    // The admin check only.
    expect(agentCalls().map(([input]) => pathOf(input))).toEqual(['/debug/agent/status']);
  });

  it('falls back to the visitor lane when the admin check is refused, and says the session expired', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    adminStatus = 401;
    renderAt(PAGE);
    // The public door is closed here, so the visitor's page is the closed door, with the admin menu.
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull();
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · expired ▾$/);
    const menu = await openAdminMenu();
    expect(within(menu).getByTestId('admin-expired')).toHaveTextContent(/sign in again on \/debug/);
    expect(within(menu).getByRole('link', { name: '/debug' })).toHaveAttribute('href', '/debug');
    expect(menu).toHaveTextContent('# the check answered unauthorized');
    expect(agentCalls().map(([input]) => pathOf(input))).toEqual(['/debug/agent/status']);
  });

  it('falls back the same way without an answer (an expired Access session), and keeps the hint', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    adminStatus = 'unreachable';
    renderAt(PAGE);
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · expired ▾$/);
    // The next sign-in on `/debug` sets the hint anyway.
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBe('1');
    const menu = await openAdminMenu();
    expect(menu).toHaveTextContent('# the check answered unreachable');
  });

  it('clears the hint and falls back when the admin lane refuses the session', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubFetch(401);
    renderAt(PAGE);
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    await waitFor(() => expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull());
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · expired ▾$/);
  });

  it('reads AGENT_ENABLED off as a visitor does, and names the switch in the admin menu only', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    // The admin gate answers before the kill switch: `not_enabled` means the admin got through.
    adminStatus = 404;
    stubFetch(404, { detail: 'not_enabled', ref: 'r-off' });
    renderAt(PAGE);
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('the assistant is closed right now. please try again later.');
    expect(alert).not.toHaveTextContent('AGENT_ENABLED');
    // The check's answer stands for the chat's own: the switched-off status is asked once.
    const statusCalls = () =>
      agentCalls().filter(([input]) => pathOf(input) === '/debug/agent/status');
    expect(statusCalls()).toHaveLength(1);
    const menu = await openAdminMenu();
    expect(within(menu).getByRole('region', { name: 'diagnostics' })).toHaveTextContent(
      'not_enabled · the agent chat is switched off on this server (AGENT_ENABLED)'
    );
    // Opening the menu reads it once more, for the meters.
    await waitFor(() => expect(statusCalls()).toHaveLength(2));
  });

  it('switches to the visitor view and back from the admin menu, remembered for the tab', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    const menu = await openAdminMenu();
    fireEvent.click(within(menu).getByRole('button', { name: 'view as visitor' }));
    // The public door is closed here: the visitor's page, with the way back.
    expect(await screen.findByText(/the assistant is closed right now/)).toBeInTheDocument();
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin · as visitor ▾$/);
    expect(sessionStorage.getItem(VIEW_AS_VISITOR_KEY)).toBe('1');

    const back = await openAdminMenu();
    const view = within(back).getByRole('button', { name: 'view as visitor' });
    expect(view).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(view);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(screen.getByTestId('admin-menu')).toHaveTextContent(/^admin ▾$/);
    expect(sessionStorage.getItem(VIEW_AS_VISITOR_KEY)).toBeNull();
    // A new session on the admin lane: the first one was deleted with the switch.
    const opens = agentCalls().filter(
      ([input, init]) =>
        pathOf(input) === '/debug/agent/sessions' && (init as RequestInit).method === 'POST'
    );
    expect(opens).toHaveLength(2);
    expect(
      agentCalls().some(
        ([input, init]) =>
          pathOf(input) === '/debug/agent/sessions/S1' && (init as RequestInit).method === 'DELETE'
      )
    ).toBe(true);
  });

  it('asks before the visitor view drops a session with data', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderAt(PAGE);
    await parseAndSummarize();
    const menu = await openAdminMenu();
    fireEvent.click(within(menu).getByRole('button', { name: 'view as visitor' }));
    expect(confirm).toHaveBeenCalledWith(
      'switch the view? the session ends here, and its data and plots cannot be restored'
    );
    // Refused: the chat and its data stay.
    expect(screen.getByText(SUMMARY)).toBeInTheDocument();
    expect(sessionStorage.getItem(VIEW_AS_VISITOR_KEY)).toBeNull();
    confirm.mockRestore();
  });

  it('offers the other libraries as links when the pair is not eligible', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubFetch(422, { detail: 'not_eligible', ref: 'r1' });
    renderAt(PAGE);
    expect(await screen.findByText('not eligible')).toBeInTheDocument();
    // The reason stands inside the chat's frame, below its header row with the library menu.
    const frame = screen.getByRole('region', { name: 'Chat' });
    expect(frame).toContainElement(screen.getByRole('alert'));
    expect(frame).toContainElement(libraryChip());
    // The tab names the page in every phase, not only once a session is open.
    await waitFor(() => expect(document.title).toMatch(/^agent · .+ \| anyplot\.ai$/));
    // No session exists to switch, so a pick opens the page anew with its own session.
    const menu = await openLibraryMenu();
    await waitFor(() =>
      expect(within(menu).getByRole('link', { name: 'seaborn' })).toHaveAttribute(
        'href',
        '/agent?spec=scatter-basic&library=seaborn&language=python'
      )
    );
    expect(within(menu).getByRole('button', { name: 'matplotlib' })).toBeDisabled();
    await closeLibraryMenu();
    // No session: nothing to fan out and nothing to save; the visitor's view stays.
    const admin = await openAdminMenu();
    expect(within(admin).queryByRole('button', ALL_TOGGLE)).not.toBeInTheDocument();
    expect(within(admin).queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    expect(within(admin).getByRole('button', { name: 'view as visitor' })).toBeInTheDocument();
  });

  it('walks the two steps with one click: .create_plot() confirms the data, then plots', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    // Before data the status line names the step and the data; the how-to is behind the start
    // item's ⓘ, not in a paragraph on the page (2026-11-02).
    expect(screen.getByTestId('data-step')).toHaveTextContent(/^>>> step 1 of 2 · your data$/);
    expect(screen.queryByText(/check the data and the bindings/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'How the chat takes data' })).toBeInTheDocument();

    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(create);
    // From the moment data is stored, the one action is `.create_plot() →`, filled at the
    // composer's end; `.example_data()` stays in its place, inert. No `.send()`: Enter sends.
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
    expect(create).toHaveAttribute('type', 'button');
    // Before the first plot, the chat's own feedback waits at the status line's end.
    expect(statusActions()).toEqual(['.feedback()']);
    // The data card stands in the thread after the paste it came from; the summary follows it.
    const card = screen.getByTestId('data-card');
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(thread).toContainElement(card);
    const follows = (first: Element, second: Element) =>
      !!(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);
    expect(follows(screen.getByTestId('paste-item'), card)).toBe(true);
    expect(follows(card, screen.getByText(SUMMARY))).toBe(true);
    // The first binding setup after a paste dropped no confirmation: nothing to name.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'step 1 of 2 · check the data and the bindings above, then .create_plot()'
    );
    expect(create).toHaveAccessibleDescription(
      'step 1 of 2 · check the data and the bindings above, then .create_plot()'
    );
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the first plot should do'
    );

    // One data chapter so far, and the card names its version.
    expect(chapters()).toEqual(['data']);
    expect(screen.getByTestId('data-card-label')).toHaveTextContent(
      /^data v1 · pasted · 2 rows × 2 cols/
    );

    holdNextTurn = true;
    fireEvent.click(create);
    // The run starts, the confirmation first. The card stays open in its chapter, no header
    // pins it, and the plot turn opens the plot chapter below it.
    await waitFor(() =>
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot'])
    );
    expect(screen.getByTestId('data-card')).toBe(card);
    expect(screen.queryByTestId('data-pinned')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Show the data' })).not.toBeInTheDocument();
    expect(currentStep()).toBe(2);
    expect(chapters()).toEqual(['data', 'plot']);
    // The button waits in its place, inert, while its run lasts; `.stop()` stands at the status
    // line's end.
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() → (inert)']);
    expect(screen.getByRole('button', { name: 'Create plot' })).toBe(create);
    expect(statusActions()).toEqual(['.stop()']);
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 2: the data is confirmed; create the plot below'
    );
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_confirmed', {
      size_bucket: 'lt_1kb',
    });
    // While it plots, the status line says so, how long it runs and how long it usually takes, in
    // the step's words' place; the plot button's description, the same line, reads no clock.
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · drawing your plot · \d+:\d\d · usually 1–3 min$/
    );
    expect(create).toHaveAccessibleDescription('step 2 of 2 · drawing your plot · usually 1–3 min');
    // The working line at the thread's foot says the same, with the same clock.
    expect(screen.getByTestId('working-line')).toHaveTextContent(/^drawing your plot · \d+:\d\d$/);
    expect(screen.queryByText(/create the plot as it is/)).not.toBeInTheDocument();
    expect(lastAction()).toHaveTextContent(/^❯\.create_plot\(\)# matplotlib$/);

    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    // The confirmed data has a plot here: the same button updates it with the box's text, inert
    // while the box is empty; `.start_over()` stands at the status line's end, and the line
    // names the data the plot was made from.
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.update_plot() → (inert)']);
    expect(screen.getByRole('button', { name: 'Update plot' })).toBe(create);
    expect(statusActions()).toEqual(['.start_over()']);
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · data v1 fits · 2 rows · 2 columns$/
    );
    expect(screen.getByRole('button', { name: 'Start over' })).toHaveAccessibleDescription(
      'new from the catalogue plot; keeps your remembered decisions'
    );

    // The thread names the button as it read, not the action it sends.
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Start over' }), { detail: 1 });
    await waitFor(() => expect(lastAction()).toHaveTextContent(/^❯\.start_over\(\)# matplotlib$/));
    // The status line at the frame's foot always stands: the run's words take the data's place.
    expect(statusActions()).toEqual(['.stop()', '.start_over()']);
    expect(screen.getByRole('button', { name: 'Start over' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · drawing your plot · \d+:\d\d · usually 1–3 min$/
    );
    releaseTurn?.();
    await turnEnded();
    // The card keeps the run's clock as the plot shipped (`ready in`).
    const summaries = screen.getAllByTestId('result-summary');
    expect(summaries[summaries.length - 1]).toHaveTextContent(/^ready in \d+:\d\d · /);
  });

  it("goes back to step 1 with the dropdowns the turn's done reports, the plot button acting again", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    expect(bindingsLine()).toHaveTextContent(/^x \(across\): hours · y \(up\): score$/);

    // Text after the plot goes as a turn, whatever it asks for.
    sendFromComposer('swap x and y');
    expect(await screen.findByText('Swapped.')).toBeInTheDocument();
    await turnEnded();
    // The binding change dropped the confirmation: the plot button acts with an empty box again,
    // and makes the next version from the data as shown, from the catalogue plot.
    const update = screen.getByRole('button', { name: 'Update plot' });
    expect(update).not.toHaveAttribute('aria-disabled');
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.update_plot() →']);
    expect(screen.queryByRole('button', { name: 'Start over' })).not.toBeInTheDocument();
    expect(update).toHaveAccessibleDescription(
      'back to step 1 of 2 · bindings changed · check them above, then .update_plot() new from the catalogue plot; keeps your remembered decisions'
    );
    // A binding change is no new data version: the card stays where it is, in the first chapter,
    // while the turn that changed the bindings opens a data chapter of its own.
    expect(foldedData()).toEqual([]);
    expect(chapters()).toEqual(['data', 'plot', 'data']);
    expect(cardAtTheEnd()).toBe(false);
    // The root's binding change dropped the confirmation: the step line says so, and only it.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · bindings changed · check them above, then .update_plot()'
    );
    expect(bindingsLine()).toHaveTextContent(/^x \(across\): score · y \(up\): hours$/);
    openBindings();
    expect(screen.getByLabelText(/^x/)).toHaveValue('score');
    expect(screen.getByLabelText(/^y/)).toHaveValue('hours');
    expect(currentStep()).toBe(1);
    expect(lastTurn()).toEqual({ text: 'swap x and y' });
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the next plot should do'
    );
  });

  it('summarizes the data first, then shows a change to it with .undo()', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await attachAndSend('hours,score\n1.5,52 %\n2.0,58 %\n');
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    const thread = screen.getByRole('log', { name: 'Conversation' });
    // The start item opens the thread and stays first; the paste is the first turn after it, its
    // card follows, and the summary needs no line of its own.
    expect(thread.firstElementChild).toBe(screen.getByTestId('start-item'));
    expect(thread.children[1]).toHaveTextContent(/^# data$/);
    expect(thread.children[2]).toHaveTextContent(/^❯▤ table · 3 lines · \d+ B$/);
    expect(thread).not.toHaveTextContent('.summarize_data()');
    await turnEnded();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the first plot should do'
    );

    // A correction in words, before the plot: the card shows it in place. Enter sends a turn
    // without confirming anything; no `.send()` comes with the text, nothing in the row moves.
    sendFromComposer('das ist prozent');
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();
    const change = await screen.findByTestId('data-change');
    await turnEnded();
    expect(within(change).getByText('# changed')).toBeInTheDocument();
    expect(within(change).getByText(PREPARED.changes[0])).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
    // Nothing was confirmed yet, so nothing was lost.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    const create = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(create);
    fireEvent.click(create);
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    // The card stayed open through the plot, its change and `.undo()` at hand; the change in
    // words moved it below its turn, and the version before folded where it stood.
    expect(chapters()).toEqual(['data', 'plot']);
    expect(foldedData()).toEqual(['data v1 · pasted · 2 rows × 2 cols']);
    expect(screen.getByTestId('data-card-label')).toHaveTextContent(
      /^data v2 · changed · 2 rows × 2 cols/
    );
    const undo = within(screen.getByTestId('data-change')).getByRole('button', { name: '.undo()' });
    expect(undo).toBeEnabled();

    // `.undo()` on the card above the plot: an undo is step 1 again, and its version moves the
    // card to the thread's end as a new data chapter (owner, 2026-11-07). The focus follows the
    // card: `.undo()` waits now (version 1 has nothing before it), so it lands on the label.
    undo.focus();
    fireEvent.click(undo);
    expect(await screen.findByText('# undone · back to the version before')).toBeInTheDocument();
    expect(chapters()).toEqual(['data', 'plot', 'data']);
    expect(cardAtTheEnd()).toBe(true);
    expect(foldedData()).toEqual([
      'data v1 · pasted · 2 rows × 2 cols',
      'data v2 · changed · 2 rows × 2 cols',
    ]);
    expect(screen.getByTestId('data-card-label')).toHaveFocus();
    // One line says what to do, the step line above the composer; no notice repeats it above.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · data changed · check it above, then plot the new data'
    );
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    // The undone data with a plot here: the plot button acts with an empty box again, named for
    // the data that changed.
    expect(composerButtons()).toEqual(['.example_data() (inert)', 'plot the new data']);
    expect(screen.getByRole('button', { name: 'Plot the new data' })).toBe(create);
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();
    expect(screen.getByRole('cell', { name: '52' })).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_undo', { version: '1' });
    // An undo asks for no new summary.
    expect(confirmAndTurns()).toEqual([
      'summarize_data',
      'text: das ist prozent',
      'confirm',
      'create_plot',
    ]);

    // `.start_over()` stands beside it: the catalogue plot without waiting for a run that may
    // change the latest plot instead.
    expect(statusActions()).toEqual(['.start_over()']);

    // The thread names the button as it read: the plot of the new data, not `.create_plot()`.
    // Its action is its own, which the server starts from the latest plot when its guard allows.
    fireEvent.click(screen.getByRole('button', { name: 'Plot the new data' }), { detail: 1 });
    await waitFor(() => expect(lastAction()).toHaveTextContent(/^❯plot the new data# matplotlib$/));
    await turnEnded();
    expect(confirmAndTurns().slice(-2)).toEqual(['confirm', 'plot_new_data']);
  });

  it('sends a pasted formula to the chat, whose table becomes version 1', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    const textbox = await screen.findByLabelText('Message');
    // Without data the one box names its own ways in, a table or a file, and the highlighted line
    // above it the other two; the how-to paragraph under the card is gone (2026-11-02).
    expect(textbox).toHaveAttribute('placeholder', 'paste a table or drop a file');
    expect(screen.getByTestId('data-line')).toHaveTextContent(
      /^# no data at hand\?\.example_data\(\)·\.open\(\)a file$/
    );
    expect(screen.getByTestId('data-line')).toHaveAttribute('data-highlighted', 'true');
    expect(screen.queryByText(/paste your data above/)).not.toBeInTheDocument();

    // One line is a message: the paste lands in the box as typed text, and Enter sends it.
    await waitFor(() => expect(textbox).toBeEnabled());
    expect(fireEvent.paste(textbox, { clipboardData: { files: [], getData: () => FORMULA } })).toBe(
      true
    );
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    sendFromComposer(FORMULA);
    // The assistant computes it: its table is the first data, and the box is free again.
    expect(await screen.findByText('I generated 200 rows from y = sin(x).')).toBeInTheDocument();
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(within(thread).getByText(FORMULA)).toBeInTheDocument();
    expect(textbox).toHaveValue('');
    expect(turnBodies()).toEqual([{ text: FORMULA }]);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    const change = await screen.findByTestId('data-change');
    expect(within(change).getByText('# changed')).toBeInTheDocument();
    expect(within(change).getByText(GENERATED.changes[0])).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
    expect(bindingsLine()).toHaveTextContent(/^x \(across\): x · /);
    expect(screen.getByRole('cell', { name: '-1.2246468e-16' })).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    await turnEnded();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await waitFor(() => expect(create).toBeEnabled());
    fireEvent.click(create);
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    // The computed table is the session's first version, its card open beside the plot.
    expect(screen.getByTestId('data-card-label')).toHaveTextContent(/^data v1 · generated · /);
  });

  it('keeps the confirmed data open in its chapter above the plot, with no header pinned', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    const card = within(screen.getByTestId('data-card'));
    expect(card.getByRole('cell', { name: '52' })).toBeInTheDocument();
    expect(card.getByTestId('bindings-line')).toHaveTextContent(/^x \(across\): hours · /);
    expect(screen.queryByTestId('data-pinned')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^(Show|Hide|Go to) the data$/ })).toBeNull();
    // The data chapter holds the card, the plot chapter the plot below it.
    const [data, plot] = screen.getAllByRole('heading', { level: 3 });
    expect(data).toHaveTextContent('# data');
    expect(plot).toHaveTextContent('# plot');
    const follows = (first: Element, second: Element) =>
      !!(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);
    expect(follows(data, screen.getByTestId('data-card'))).toBe(true);
    expect(follows(screen.getByTestId('data-card'), plot)).toBe(true);
    expect(follows(plot, screen.getByRole('article', { name: 'Plot version 1' }))).toBe(true);
    // The page keeps the focus and a jump clear of the site's sticky masthead.
    expect(
      [...document.querySelectorAll('style')].some(style =>
        /scroll-padding-top:\s*56px/.test(style.textContent ?? '')
      )
    ).toBe(true);
    expect(currentStep()).toBe(2);
    expect(screen.getByRole('button', { name: 'Start over' })).toBeEnabled();
  });

  it('goes back to step 1 with the card open when a binding changes in step 2', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    const card = screen.getByTestId('data-card');
    openBindings();
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });

    const update = screen.getByRole('button', { name: 'Update plot' });
    await waitFor(() => expect(currentStep()).toBe(1));
    // The card stays open where it is: a binding change makes no data version.
    expect(screen.getByTestId('data-card')).toBe(card);
    expect(foldedData()).toEqual([]);
    await untilActive(update);
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.update_plot() →']);
    // The loss is named once, in the plot button's description, and no notice in the thread
    // repeats it.
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · bindings changed · check them above, then .update_plot()'
    );
    expect(lossNotice()).not.toBeInTheDocument();

    // Back and forth: the confirmation is gone already, and the step line still names it.
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'score' } });
    await waitFor(() => expect(screen.getByLabelText(/^y/)).toBeEnabled());
    expect(screen.getByTestId('data-step')).toHaveTextContent('bindings changed');

    // One click takes the data again, and the row's reason goes with the step; the card stays.
    await untilActive(update);
    fireEvent.click(update);
    await waitFor(() => expect(currentStep()).toBe(2));
    await turnEnded();
    expect(screen.getByTestId('data-card')).toBe(card);
    expect(screen.getByTestId('data-step')).not.toHaveTextContent('bindings changed');
  });

  it('names the loss for the data the card shows after it, never for a new paste', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    openBindings();
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });
    await waitFor(() => expect(screen.getByLabelText(/^y/)).toBeEnabled());
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · bindings changed · check them above, then .update_plot()'
    );

    // A data request after the loss: the step line names the change the preview shows.
    sendFromComposer('read score as prozent');
    expect(await screen.findByText('I read score as numbers.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · data changed · check it above, then plot the new data'
    );

    // A new paste is data nobody confirmed: plain step 1, and the plot button names it new data.
    await attachAndSend('hours,score\n3,70\n4,80\n');
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 1 of 2 · check the data and the bindings above, then plot the new data$/
    );
    expect(lossNotice()).not.toBeInTheDocument();
  });

  it('confirms and then plots in one click, and Enter never confirms', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const box = screen.getByLabelText('Message');
    // Enter in an empty box sends nothing; Enter with text sends a turn, no confirmation.
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(confirmAndTurns()).toEqual(['summarize_data']);
    sendFromComposer('what is the mean score?');
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'text: what is the mean score?']);
    expect(currentStep()).toBe(1);

    // A pointer click moves no focus into the box, so a phone opens no keyboard.
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }), { detail: 1 });
    expect(box).not.toHaveFocus();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    expect(confirmAndTurns()).toEqual([
      'summarize_data',
      'text: what is the mean score?',
      'confirm',
      'create_plot',
    ]);
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(within(thread).getByText('.create_plot()')).toBeInTheDocument();
  });

  it('starts no plot when the confirmation is refused, and shows why under the composer', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    let refusal = json(422, { detail: 'no_dataset', ref: 'r-c' });
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
      if (new URL(input).pathname.endsWith('/dataset/confirm')) return refusal.clone();
      return base(input, init);
    });
    renderAt(PAGE);
    await parseAndSummarize();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/^parse the data first$/);
    // Nothing plotted, the note still in the box, the button ready for a retry.
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm']);
    expect(screen.getByLabelText('Message')).toHaveValue('log scale on y');
    await untilActive(screen.getByRole('button', { name: 'Create plot' }));
    expect(currentStep()).toBe(1);
    expect(screen.getByTestId('data-card')).toBeInTheDocument();

    // A server error with an empty box: no plot from the catalogue code either.
    refusal = json(500, { detail: 'internal', ref: 'r-c2' });
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ref r-c2'));
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'confirm']);
    expect(screen.queryByRole('article', { name: /^Plot version/ })).not.toBeInTheDocument();
    expect(currentStep()).toBe(1);
  });

  it('keeps a note in the thread when its turn is refused right after the confirmation', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    let summarized = false;
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
      const turn = new URL(input).pathname.endsWith('/messages') && init.method === 'POST';
      if (turn && summarized) return json(429, { detail: 'rate_limited', ref: 'r-t' });
      if (turn) summarized = true;
      return base(input, init);
    });
    renderAt(PAGE);
    await parseAndSummarize();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(await within(thread).findByText(/the daily limit is reached/)).toBeInTheDocument();
    // The box is empty, and the note the user typed stands in the thread above the refusal.
    expect(within(thread).getByText('log scale on y')).toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveValue('');
  });

  it('sends a note typed before the first plot as the turn that makes it, after the confirmation', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'text: log scale on y']);
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(within(thread).getByText('log scale on y')).toBeInTheDocument();
    expect(within(thread).queryByText('.create_plot()')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveValue('');

    // This library has a plot: the plot button updates it with the box's text, and starting
    // over is one quiet click at the status line's end that says what it does.
    expect(screen.getByRole('article', { name: 'Plot version 1' })).toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask for a change, e.g. log scale on y'
    );
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Update plot' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver).not.toHaveAttribute('aria-disabled');
    expect(startOver).toHaveTextContent('.start_over()');
    expect(startOver).toHaveAccessibleDescription(
      expect.stringContaining('new from the catalogue plot; keeps your remembered decisions')
    );
    // The data the plot was made from stays open in its chapter above.
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(chapters()).toEqual(['data', 'plot']);
  });

  it('opens a new data chapter for a data request after the plot, the card before the reply', async () => {
    const scroll = vi.fn();
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      value: scroll,
      configurable: true,
      writable: true,
    });
    try {
      localStorage.setItem(ADMIN_HINT_KEY, '1');
      renderAt(PAGE);
      await parseAndPlot();
      const card = screen.getByTestId('data-card');
      expect(chapters()).toEqual(['data', 'plot']);

      // A change to the data asked for below the plot: a new data chapter, the card right after
      // the request and before the reply (owner, 2026-11-07), the version it showed folded where
      // it stood.
      const box = screen.getByLabelText('Message');
      box.focus();
      scroll.mockClear();
      sendFromComposer('das ist prozent');
      const change = await screen.findByTestId('data-change');
      await turnEnded();
      expect(chapters()).toEqual(['data', 'plot', 'data']);
      const request = screen.getByText('das ist prozent').closest('[role="log"] > *')!;
      const reply = screen.getByText('I read score as numbers.');
      expect(request.nextElementSibling).toBe(card);
      expect(card.nextElementSibling).toContainElement(reply);
      expect(cardAtTheEnd()).toBe(false);
      // The card landed above the reply, which had streamed in already: the thread held the
      // reply still (`HoldReadingPosition`, tested in ChatThread), gave the page's anchoring back,
      // and the reply, the first after the card now, is brought into view once at the nearest
      // edge, which moves nothing where it stands in view.
      await waitFor(() => expect(document.documentElement.style.overflowAnchor).not.toBe('none'));
      const replyBox = screen.getByTestId('first-reply');
      expect(replyBox).toContainElement(reply);
      expect(scroll.mock.contexts.filter(context => context === replyBox)).toHaveLength(1);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'nearest' });
      // The same card, moved, not a new one; the focus stays in the box the request came from.
      expect(screen.getByTestId('data-card')).toBe(card);
      expect(box).toHaveFocus();
      expect(foldedData()).toEqual(['data v1 · pasted · 2 rows × 2 cols']);
      expect(screen.getByTestId('data-card-label')).toHaveTextContent(
        /^data v2 · changed · 2 rows × 2 cols/
      );
      expect(within(change).getByText('# changed')).toBeInTheDocument();
      expect(within(change).getByRole('button', { name: '.undo()' })).toBeEnabled();
      expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
      expect(currentStep()).toBe(1);
      // Step 1 again with a plot here: the plot button acts with an empty box, named for what
      // it does now: the next version from the changed data. `.start_over()` beside it is the
      // catalogue plot instead, since the button may change the latest plot.
      expect(composerButtons()).toEqual(['.example_data() (inert)', 'plot the new data']);
      expect(statusActions()).toEqual(['.start_over()']);
      // The step line alone says it: no notice right above it in the thread.
      expect(lossNotice()).not.toBeInTheDocument();
      expect(screen.getByTestId('data-step')).toHaveTextContent(
        'back to step 1 of 2 · data changed · check it above, then plot the new data'
      );

      // The older version opens read-only from its label: its preview, nothing to press.
      const older = screen.getByRole('button', { name: 'Data v1, pasted, 2 rows by 2 columns' });
      fireEvent.click(older);
      const stub = screen.getByTestId('data-stub');
      expect(older).toHaveAttribute('aria-expanded', 'true');
      expect(within(stub).getByRole('cell', { name: '52' })).toBeInTheDocument();
      expect(within(stub).getAllByRole('button')).toEqual([older]);

      // One click: the changed data confirmed, then a new version for it (`plot_new_data`, which
      // the server starts from the latest plot when its guard allows), which opens the next plot
      // chapter below the card.
      const create = screen.getByRole('button', { name: 'Plot the new data' });
      await untilActive(create);
      fireEvent.click(create);
      await waitFor(() => expect(screen.getAllByText('Here is your plot.')).toHaveLength(2));
      await turnEnded();
      expect(confirmAndTurns().slice(-2)).toEqual(['confirm', 'plot_new_data']);
      expect(composerButtons()).toEqual(['.example_data() (inert)', '.update_plot() → (inert)']);
      expect(statusActions()).toEqual(['.start_over()']);
      expect(chapters()).toEqual(['data', 'plot', 'data', 'plot']);
    } finally {
      delete (Element.prototype as Partial<Element>).scrollIntoView;
    }
  });

  it('holds step 1 while a table read from text waits, whatever a turn reports', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    await transcribeInStep2();
    expect(currentStep()).toBe(1);

    // The server keeps its confirmation of the stored data, and the turn's sync says so;
    // the text still goes as a turn.
    sendFromComposer('what columns are there?');
    expect(await screen.findByText('Two columns: hours and score.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ text: 'what columns are there?' });
    expect(currentStep()).toBe(1);
    expect(screen.getByTestId('transcription-card')).toBeInTheDocument();
    // The stored data's card stays open above it until the decision.
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    // The plot button waits for the decision, and its description, the status line, says so.
    const update = screen.getByRole('button', { name: 'Update plot' });
    expect(update).toHaveAttribute('aria-disabled', 'true');
    expect(update).toHaveAccessibleDescription(
      expect.stringContaining('step 1 of 2 · decide on the table first: .use() or .discard()')
    );
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the next plot should do'
    );

    // Discarded, the stored data is the confirmed data again, with its plot.
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(currentStep()).toBe(2);
    expect(screen.getByRole('button', { name: 'Start over' })).toBeEnabled();
  });

  it('returns to step 2 when a table read from text is discarded at once', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    await transcribeInStep2();
    expect(currentStep()).toBe(1);

    // The transcription stored nothing and the server kept its confirmation: discarding it
    // is back where the user was, with no turn in between.
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(currentStep()).toBe(2);
    expect(screen.getByTestId('data-step')).toHaveTextContent('data v1 fits');
    expect(screen.getByRole('button', { name: 'Start over' })).toBeEnabled();
    expect(screen.queryByTestId('transcription-card')).not.toBeInTheDocument();
  });

  it('leaves the composer focus alone when step 2 returns by itself', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    await transcribeInStep2();
    expect(currentStep()).toBe(1);

    const box = screen.getByLabelText('Message');
    box.focus();
    // A turn's sync confirms the data again while the table still waits: step 1 holds.
    sendFromComposer('what columns are there?');
    expect(await screen.findByText('Two columns: hours and score.')).toBeInTheDocument();
    await turnEnded();
    expect(currentStep()).toBe(1);
    expect(box).toHaveFocus();

    // Discarding the table brings step 2 back with no click of the user's: the next key press
    // still types into the box.
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(currentStep()).toBe(2);
    expect(box).toHaveFocus();
    expect(screen.getByRole('button', { name: 'Start over' })).not.toHaveFocus();
  });

  it('never spends a second key press on stopping the run it started', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(create);
    create.focus();
    holdNextTurn = true;

    // Enter on the focused button. It stays in its place, inert, and keeps the focus; `.stop()`
    // is a button of its own at the status line's end, so a second Enter stops nothing.
    fireEvent.click(create, { detail: 0 });
    const stop = await screen.findByRole('button', { name: 'Stop' });
    expect(stop).not.toBe(create);
    expect(stop).not.toHaveFocus();
    expect(create).toHaveFocus();
    await waitFor(() => expect(create).toHaveAttribute('aria-disabled', 'true'));
    fireEvent.click(create, { detail: 0 });

    await waitFor(() => expect(releaseTurn).not.toBeNull());
    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
    expect(agentCalls().some(([input]) => String(input).endsWith('/cancel'))).toBe(false);
    // The same button reads `.update_plot() →` now, and the focus is still on it.
    expect(screen.getByRole('button', { name: 'Update plot' })).toBe(create);
    expect(create).toHaveFocus();
  });

  it('moves the focus on to the message box when the .stop() it held goes with the run', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(create);
    holdNextTurn = true;
    fireEvent.click(create);
    const stop = await screen.findByRole('button', { name: 'Stop' });
    stop.focus();

    await waitFor(() => expect(releaseTurn).not.toBeNull());
    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.queryByRole('button', { name: 'Stop' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveFocus();
  });

  it("holds back the composer's plot button while a parse runs", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver).not.toHaveAttribute('aria-disabled');

    await attachAndSend('slow,data\n1,2\n');
    await waitFor(() => expect(releaseParse).not.toBeNull());
    expect(startOver).toHaveAttribute('aria-disabled', 'true');

    // A new parse is new data: step 1 again, with the plot button filled for it and named so.
    releaseParse?.();
    expect(await screen.findByRole('button', { name: 'Plot the new data' })).toBeInTheDocument();
    expect(currentStep()).toBe(1);
  });

  it('offers a reload when the session open got no answer', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubFetch();
    const answered = fetchMock as unknown as (input: string, init?: RequestInit) => Response;
    // The admin check answered; every BFF call after it meets the Access redirect, while the
    // public catalogue still answers.
    let checked = false;
    fetchMock = vi.fn(async (input: string, init: RequestInit = {}) => {
      if (String(input).includes('/debug/agent/')) {
        if (!checked && String(input).endsWith('/debug/agent/status')) {
          checked = true;
          return answered(input, init);
        }
        throw new TypeError('Failed to fetch');
      }
      return answered(input, init);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderAt(PAGE);
    expect(await screen.findByText('error · unreachable')).toBeInTheDocument();
    // The error stands inside the chat's frame, below its header row.
    expect(screen.getByRole('region', { name: 'Chat' })).toContainElement(
      screen.getByRole('alert')
    );
    // A reload checks the admin anew: `/agent` is not behind Access and reloads by itself never.
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();
  });
});

describe('AgentChatPage start item', () => {
  const follows = (first: Element, second: Element) =>
    !!(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);

  it('shows the catalogue plot in the start item, in the library in use, and opens it large', async () => {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation(async (input: string, init?: RequestInit) =>
      new URL(input).pathname.endsWith('/sessions/S1/library')
        ? json(200, {
            session_id: 'S1',
            eligibility: { eligible: true, status: 'clean', reasons: [] },
          })
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    const thumbnail = await screen.findByRole('button', {
      name: 'Show the matplotlib catalogue plot large',
    });
    // The thread's first item holds it, the header row no longer: the row keeps the title, the
    // two dropdowns and the admin menu, and every ⓘ of the start stands in the thread too.
    const start = screen.getByTestId('start-item');
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(thread.firstElementChild).toBe(start);
    expect(start).toContainElement(thumbnail);
    expect(start).toHaveTextContent(/^You came from Basic Scatter Plot\. It needs/);
    for (const name of ['Columns the plot expects', 'How the chat takes data']) {
      expect(start).toContainElement(screen.getByRole('button', { name }));
    }
    expect(follows(screen.getByTestId('admin-menu'), thread)).toBe(true);
    // The site theme's preview, from the catalogue's responsive files.
    expect(thumbnail.querySelector('source')).toHaveAttribute(
      'srcset',
      expect.stringContaining('/scatter-basic/matplotlib/plot-light_400.webp 400w')
    );
    expect(thumbnail.querySelector('img')).toHaveAttribute(
      'src',
      'https://img.test/scatter-basic/matplotlib/plot-light_800.png'
    );

    thumbnail.focus();
    fireEvent.click(thumbnail);
    const dialog = await screen.findByRole('dialog', { name: '# Basic Scatter Plot · matplotlib' });
    expect(
      within(dialog).getByRole('img', {
        name: 'Basic Scatter Plot in matplotlib, the plot from the catalogue',
      })
    ).toBeInTheDocument();
    fireEvent.keyDown(dialog, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await waitFor(() => expect(thumbnail).toHaveFocus());

    // It follows a library switch.
    await pickInMenu('seaborn');
    expect(
      await screen.findByRole('button', { name: 'Show the seaborn catalogue plot large' })
    ).toBeInTheDocument();
  });

  /** The ⓘ's lines once it is open. */
  async function expectedColumnsShown() {
    const info = await screen.findByRole('button', { name: 'Columns the plot expects' });
    expect(info).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(info);
    const details = await screen.findByRole('dialog', { name: 'Columns the plot expects' });
    return within(within(details).getByTestId('expected-columns'))
      .getAllByRole('listitem')
      .map(item => item.textContent);
  }

  it("names the spec's roles as chips in plain words, and in full behind the ⓘ after them", async () => {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation(async (input: string, init?: RequestInit) =>
      new URL(input).pathname.endsWith('/debug/agent/sessions') && init?.method === 'POST'
        ? json(200, {
            session_id: 'S1',
            eligibility: { eligible: true, status: 'clean', reasons: [] },
            roles: [
              { ...DATASET.roles[0], kinds: ['numeric', 'datetime'] },
              { ...DATASET.roles[1], variadic: true },
              {
                name: 'series',
                kinds: ['categorical'],
                required: false,
                variadic: false,
                description: 'one colour per group',
              },
            ],
          })
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    // What a column holds, never a dtype; a family takes one or more, an optional role says so.
    const chips = within(screen.getByRole('list', { name: 'What the plot needs' }));
    expect(chips.getAllByRole('listitem').map(chip => chip.textContent)).toEqual([
      'x · numbers or dates',
      'y · numbers, one or more',
      'series · categories, optional',
    ]);
    // The ⓘ says the kinds in the chips' words.
    expect(await expectedColumnsShown()).toEqual([
      'x (numbers or dates) · x values',
      'y (numbers, one column each) · y values',
      'series (categories, optional) · one colour per group',
    ]);
  });

  it("falls back to the spec's data bullets, without the meta lines, when the open names no roles", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    // No chips without roles: the ⓘ with the bullets ends the sentence.
    expect(screen.queryByRole('list', { name: 'What the plot needs' })).not.toBeInTheDocument();
    expect(await expectedColumnsShown()).toEqual([
      'x (numeric) - Independent variable values plotted on the horizontal axis',
      'y (numeric) - Dependent variable values plotted on the vertical axis',
    ]);
  });

  it('repeats no control of the composer, and stays first in the thread once data arrives', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    const start = screen.getByTestId('start-item');
    // `.example_data()` and `.open()` are the data line's, right above the box: the item points there.
    expect(start).toHaveTextContent(/drop a file or paste a table below$/);
    expect(within(start).queryByRole('button', { name: 'Make example data' })).toBeNull();
    expect(within(start).queryByRole('button', { name: 'Open a data file' })).toBeNull();
    // Inside the polite log, a title or a picture that arrives late is no news to read out.
    expect(start).toHaveAttribute('aria-live', 'off');

    await parseAndSummarize();
    // A message in the thread: nothing vanishes, the talk follows it.
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(thread.firstElementChild).toBe(start);
    expect(start).toHaveTextContent(/^You came from Basic Scatter Plot\./);
    expect(follows(start, screen.getByTestId('paste-item'))).toBe(true);
    expect(follows(start, screen.getByText(SUMMARY))).toBe(true);
  });

  // A visitor's open and its source are recorded: AgentChatPage.public.test.tsx.
  it("drops an admin's source from the URL without recording the open", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&source=plot_of_the_day`);
    await screen.findByLabelText('Message');
    await waitFor(() => expect(screen.getByTestId('location')).not.toHaveTextContent('source='));
    expect(screen.getByTestId('location')).toHaveTextContent(PAGE);
    expect(analytics.trackEvent).not.toHaveBeenCalledWith('agent_open', expect.anything());
  });
});

describe('AgentChatPage card in the thread', () => {
  const follows = (first: Element, second: Element) =>
    !!(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);
  /** `scrollIntoView` as a spy (jsdom has none), restored by `done`. */
  function spyScroll() {
    const scroll = vi.fn();
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      value: scroll,
      configurable: true,
      writable: true,
    });
    return {
      scroll,
      done: () => delete (Element.prototype as Partial<Element>).scrollIntoView,
    };
  }

  it('moves the card below a paste in step 2 and leaves a stub of the data it showed', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    // Step 2: the card stays open after its paste.
    const before = screen.getByTestId('data-card');
    expect(follows(screen.getByTestId('paste-item'), before)).toBe(true);
    // Inside the polite log, the card's own changes are no news to read out.
    expect(before).toHaveAttribute('aria-live', 'off');

    await attachAndSend('hours,score\n3,70\n4,80\n');
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    const stub = screen.getByTestId('data-stub');
    expect(within(stub).getByRole('button')).toHaveTextContent(
      /^▸data v1 · pasted · 2 rows × 2 cols$/
    );
    const [first, second] = screen.getAllByTestId('paste-item');
    const card = screen.getByTestId('data-card');
    expect(card).not.toBe(before);
    // The first paste, its folded version, the plot of that data, then a new data chapter with
    // the new paste and its card.
    expect(follows(first, stub)).toBe(true);
    expect(follows(stub, screen.getByText('Here is your plot.'))).toBe(true);
    expect(follows(screen.getByText('Here is your plot.'), second)).toBe(true);
    expect(follows(second, card)).toBe(true);
    expect(chapters()).toEqual(['data', 'plot', 'data']);
    expect(screen.getByTestId('data-card-label')).toHaveTextContent(/^data v2 · pasted · /);
    // New data nobody confirmed: step 1, its card open.
    expect(currentStep()).toBe(1);
  });

  it('brings the summary after a card into view while the focus is in the composer', async () => {
    const { scroll, done } = spyScroll();
    try {
      localStorage.setItem(ADMIN_HINT_KEY, '1');
      renderAt(PAGE);
      const box = await screen.findByLabelText('Message');
      await waitFor(() => expect(box).toBeEnabled());
      box.focus();
      await attachAndSend('hours,score\n1.5,52\n2.0,58\n');
      expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
      const reply = screen.getByTestId('first-reply');
      expect(reply).toHaveTextContent(SUMMARY);
      expect(scroll.mock.contexts).toContain(reply);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'nearest' });
    } finally {
      done();
    }
  });
});

describe('AgentChatPage .example_data()', () => {
  it('offers example data as the filled button without data, as an action, inert until it arrives', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    // Before data the row holds its four places already: the plot button stands quiet and inert.
    const example = screen.getByRole('button', { name: 'Make example data' });
    await untilActive(example);
    expect(composerButtons()).toEqual(['.example_data()', '.create_plot() → (inert)']);
    expect(screen.queryByText('# no data at hand?')).not.toBeInTheDocument();

    holdNextTurn = true;
    example.focus();
    fireEvent.click(example, { detail: 0 });

    // The button stays in its place, inert, with the focus: the working line says it once, beside
    // the loader.
    const pending = await screen.findByTestId('working-line');
    expect(pending).toHaveTextContent(/^making example data$/);
    expect(within(pending).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(screen.getAllByText(/making example data/)).toHaveLength(1);
    expect(example).toHaveAttribute('aria-disabled', 'true');
    expect(example).toHaveFocus();
    fireEvent.click(example, { detail: 0 });
    expect(turnBodies()).toEqual([{ action: 'example_data' }]);
    // The thread names the page's own turn and holds the assistant's slot.
    expect(screen.getByRole('log', { name: 'Conversation' })).toHaveTextContent('.example_data()');

    releaseTurn?.();
    expect(await screen.findByText(EXAMPLE_REPLY)).toBeInTheDocument();
    await turnEnded();
    // The data is there: the line turns muted and leads with `.open()`, `.example_data()` stays
    // the same element, inert, with the focus, the plot button is the action, the card shows the
    // table, and nothing set a language.
    expect(screen.getByTestId('data-line')).toHaveTextContent(
      /^# other data\?\.open\(\)·\.example_data\(\)$/
    );
    expect(screen.getByRole('button', { name: 'Make example data' })).toBe(example);
    expect(example).toHaveFocus();
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
    expect(bindingsLine()).toHaveTextContent(/^x \(across\): x · /);
    expect(screen.queryByText(/reply language/)).not.toBeInTheDocument();
  });

  it('acts again when the turn brought no data, and waits while another turn runs', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    holdNextTurn = true;
    sendFromComposer('what is the mean score?');
    const button = await screen.findByRole('button', { name: 'Make example data' });
    await waitFor(() => expect(button).toHaveAttribute('aria-disabled', 'true'));
    releaseTurn?.();
    await turnEnded();
    expect(screen.getByRole('button', { name: 'Make example data' })).not.toHaveAttribute(
      'aria-disabled'
    );
  });

  it('waits while a table waits in the box, and stays inert once a paste stored data', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    const box = await screen.findByLabelText('Message');
    await waitFor(() => expect(box).toBeEnabled());
    const example = screen.getByRole('button', { name: 'Make example data' });
    await untilActive(example);
    fireEvent.paste(box, {
      clipboardData: { files: [], getData: () => 'hours,score\n1.5,52\n2.0,58\n' },
    });
    // The attachment is data at hand: example data would only replace it.
    await waitFor(() => expect(example).toHaveAttribute('aria-disabled', 'true'));
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();

    expect(screen.getByRole('button', { name: 'Make example data' })).toBe(example);
    expect(example).toHaveAttribute('aria-disabled', 'true');
  });
});

describe('AgentChatPage leave warning', () => {
  /** A reload or a closed tab, as the browser starts it: whether the page asked to stay. */
  function unload(): boolean {
    const event = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(event);
    return event.defaultPrevented;
  }
  const deletes = () =>
    agentCalls().filter(([, init]) => (init as RequestInit | undefined)?.method === 'DELETE');
  const backLink = () => screen.getByRole('link', { name: /Basic Scatter Plot/ });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('asks nothing while the session is empty: the back link just leaves', async () => {
    const confirm = vi.spyOn(window, 'confirm');
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    expect(unload()).toBe(false);

    fireEvent.click(await screen.findByRole('link', { name: /Basic Scatter Plot/ }));
    await waitFor(() => expect(screen.queryByLabelText('Message')).not.toBeInTheDocument());
    expect(screen.getByTestId('location')).toHaveTextContent('/scatter-basic');
    expect(confirm).not.toHaveBeenCalled();
  });

  it('asks before a reload or a link drops the data, and lets its own query edits pass', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation((input: string, init?: RequestInit) =>
      new URL(input).pathname.endsWith('/sessions/S1/library')
        ? Promise.resolve(
            json(200, {
              session_id: 'S1',
              eligibility: { eligible: true, status: 'clean', reasons: [] },
            })
          )
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    expect(unload()).toBe(true);

    // A library switch writes the query on the same path: nothing to ask.
    await pickInMenu('seaborn');
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('seaborn'));
    expect(confirm).not.toHaveBeenCalled();

    // The back link to the plot, declined: the chat and its session stay.
    fireEvent.click(backLink());
    await waitFor(() => expect(confirm).toHaveBeenCalledWith(LEAVE_TEXT));
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(deletes()).toHaveLength(0);

    // Agreed: the page goes, and the session with it.
    confirm.mockReturnValue(true);
    fireEvent.click(backLink());
    await waitFor(() => expect(screen.queryByTestId('data-card')).not.toBeInTheDocument());
    expect(screen.getByTestId('location')).toHaveTextContent('/scatter-basic');
    await waitFor(() => expect(deletes()).toHaveLength(1));
    expect(unload()).toBe(false);
  });
});

describe('AgentChatPage working states', () => {
  it('says that the data is being parsed, on the chip and to a screen reader', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await attachAndSend('slow,data\n1,2\n');
    await waitFor(() => expect(releaseParse).not.toBeNull());

    const chip = screen.getByTestId('attachment');
    expect(chip).toHaveAttribute('data-status', 'sending');
    expect(chip).toHaveTextContent(/^parsing your data/);
    expect(within(chip).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove the attachment' })).toBeDisabled();
    expect(screen.getByTestId('data-step-status')).toHaveTextContent('parsing your data');

    releaseParse?.();
    await waitFor(() =>
      expect(screen.getByTestId('data-step-status')).toHaveTextContent(
        'step 1: check the data, then create the plot'
      )
    );
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
  });

  it('holds the summary turn in the thread and says why the bindings wait', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    holdNextTurn = true;
    await attachAndSend('hours,score\n1.5,52\n2.0,58\n');

    const pending = await screen.findByTestId('working-line');
    expect(pending).toHaveTextContent(/^summarizing your data$/);
    expect(within(pending).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(lastInThread()).toBe(pending);
    openBindings();
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(
      /^# bindings — wait while the assistant works$/
    );
    // One loader, in the thread: the bindings heading says why without motion of its own.
    expect(screen.getAllByTestId('loader-spinner')).toHaveLength(1);
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
    // The plot button waits in its place at the composer's end; `.stop()` at the status line's.
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() → (inert)']);
    expect(statusActions()).toEqual(['.stop()']);
    // One indicator: a turn without pipeline steps has no grid, and no clock.
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    expect(screen.queryByTestId('run-clock')).not.toBeInTheDocument();

    releaseTurn?.();
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    expect(screen.queryByTestId('working-line')).not.toBeInTheDocument();
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(
      /^# bindings — which column plays which role$/
    );
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
    await untilActive(screen.getByRole('button', { name: 'Create plot' }));
  });

  it('puts one working line in the thread for a question and for a plot run, the grid in the admin menu', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();

    holdNextTurn = true;
    sendFromComposer('what is the mean score?');
    const pending = await screen.findByTestId('working-line');
    expect(pending).toHaveTextContent(/^working on your message$/);
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    releaseTurn?.();
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    expect(screen.queryByTestId('working-line')).not.toBeInTheDocument();
    await turnEnded();

    // `.create_plot()` draws on the same line at the thread's foot, with its clock and the
    // loader beside it; the queue counter and the timeline below the thread are gone.
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    const line = await screen.findByTestId('working-line');
    expect(line).toHaveTextContent(/^drawing your plot · \d+:\d\d$/);
    expect(lastInThread()).toBe(line);
    expect(screen.queryByTestId('queue-counter')).not.toBeInTheDocument();
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    expect(screen.getAllByTestId('loader-spinner')).toHaveLength(1);
    // The run's grid is the admin menu's, for the admin alone.
    const menu = await openAdminMenu();
    expect(
      within(within(menu).getByRole('region', { name: 'progress of this turn' })).getByRole(
        'table',
        { name: 'Progress' }
      )
    ).toBeInTheDocument();
    await closeAdminMenu();
    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.queryByTestId('loader-spinner')).not.toBeInTheDocument();
    expect(screen.queryByTestId('working-line')).not.toBeInTheDocument();
  });

  it('shows one queue position, in the working line, for a text turn and for a plot run', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();

    // The next turn's stream stays open after its `queued` status, as a run that waits does.
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    let finish: (() => void) | null = null;
    let push: ((list: [string, unknown][]) => void) | null = null;
    const queuedTurn = (events: [string, unknown][]) =>
      new Response(
        new ReadableStream({
          start(controller) {
            const write = (list: [string, unknown][]) =>
              controller.enqueue(
                new TextEncoder().encode(
                  list
                    .map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
                    .join('')
                )
              );
            push = write;
            write([['status', { step: 'queued', position: 2, waiting: 3 }]]);
            finish = () => {
              write(events);
              controller.close();
            };
          },
        }),
        { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
      );
    fetchMock.mockImplementation((input: string, init: RequestInit = {}) =>
      pathOf(input).endsWith('/sessions/S1/messages') && init.method === 'POST'
        ? Promise.resolve(
            queuedTurn(
              String(init.body).includes('create_plot')
                ? [
                    ['plot', PLOT],
                    ['done', { llm_calls: 2, data_confirmed: true }],
                  ]
                : [
                    ['message', { text: 'The mean score is 55.' }],
                    ['done', { llm_calls: 1 }],
                  ]
            )
          )
        : base(input, init)
    );

    // A question waits in the queue: the working line says where (owner, 2026-11-09, option a),
    // the tab only that the service is busy, and nothing else on screen names a position.
    const mood = () => screen.getByTestId('load-mood');
    await waitFor(() => expect(mood()).toHaveTextContent(/quiet$/));
    sendFromComposer('what is the mean score?');
    const line = await screen.findByTestId('working-line');
    await waitFor(() => expect(line).toHaveTextContent(/^waiting · you are 2nd$/));
    expect(mood()).toHaveTextContent(/busy$/);
    expect(mood()).not.toHaveTextContent(/2nd|3rd/);
    expect(screen.queryByTestId('queue-counter')).not.toBeInTheDocument();
    expect(screen.getAllByText(/you are 2nd/)).toHaveLength(1);
    // The wait ends before the reply: the line says what the turn does, in the same element.
    act(() => push?.([['status', { step: 'started' }]]));
    await waitFor(() => expect(line).toHaveTextContent(/^working on your message$/));
    expect(screen.getByTestId('working-line')).toBe(line);
    expect(mood()).toHaveTextContent(/quiet$/);
    act(() => finish?.());
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();

    // A plot run waits the same way, without a clock while it waits, in the line or the footer.
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    const plotLine = await screen.findByTestId('working-line');
    await waitFor(() => expect(plotLine).toHaveTextContent(/^waiting · you are 2nd$/));
    expect(screen.queryByTestId('run-clock')).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · drawing your plot · usually 1–3 min$/
    );
    // The admin menu's grid keeps the position too, unseen while the menu is closed.
    expect(screen.getByText('queued · 2 of 3')).not.toBeVisible();
    // Out of the queue the clock starts, from the wait's end, in the line and the footer.
    act(() => push?.([['status', { step: 'started' }]]));
    await waitFor(() => expect(plotLine).toHaveTextContent(/^drawing your plot · 0:0\d$/));
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · drawing your plot · 0:0\d · usually 1–3 min$/
    );
    expect(screen.queryByText(/you are/)).not.toBeInTheDocument();
    act(() => finish?.());
    await turnEnded();
  });

  it('shows the loader while the session opens, then the chat', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    let open: () => void = () => {};
    fetchMock.mockImplementation((input: string, init: RequestInit = {}) => {
      if (new URL(input).pathname.endsWith('/debug/agent/sessions') && init.method === 'POST') {
        return new Promise<Response>(resolve => {
          open = () => void base(input, init).then(resolve);
        });
      }
      return base(input, init);
    });
    renderAt(PAGE);
    const opening = await screen.findByTestId('session-opening');
    expect(opening).toHaveTextContent(/^opening a session$/);
    // A polite status, so a screen reader hears the wait the dots show.
    expect(opening).toHaveAttribute('role', 'status');
    expect(within(opening).getByTestId('loader-spinner')).toHaveAttribute('aria-hidden', 'true');
    // The wait stands inside the chat's frame, below its header row, as the chat will.
    const frame = screen.getByRole('region', { name: 'Chat' });
    expect(frame).toContainElement(opening);
    expect(frame).toContainElement(screen.getByTestId('library-chip'));

    open();
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(screen.queryByTestId('session-opening')).not.toBeInTheDocument();
  });
});

describe('AgentChatPage step CTA', () => {
  it('keeps the four places whatever the box holds: no .send(), Enter sends', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    await untilActive(screen.getByRole('button', { name: 'Make example data' }));
    // No data, an empty box: example data is the action, and the status line names the step.
    expect(composerButtons()).toEqual(['.example_data()', '.create_plot() → (inert)']);
    expect(screen.getByTestId('data-step')).toHaveTextContent(/^>>> step 1 of 2 · your data$/);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'sin(x) please' } });
    expect(composerButtons()).toEqual(['.example_data()', '.create_plot() → (inert)']);
    // On a touch screen the `↵` in the box sends what it holds; it shows there only.
    expect(screen.getByTestId('send-return')).not.toHaveAttribute('aria-disabled');
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: '   ' } });
    expect(screen.getByTestId('send-return')).toHaveAttribute('aria-disabled', 'true');

    // With data the plot button is the action, with or without text.
    await parseAndSummarize();
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale' } });
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
  });

  it('reads a table typed into the box as data on the plot click too, as on Enter', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(create);
    fireEvent.change(screen.getByLabelText('Message'), {
      target: { value: 'hours,score\n3,70\n4,80\n5,85\n' },
    });
    fireEvent.click(create);
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    // The table went to the dataset route: no confirmation, no plot, no message with the table.
    expect(confirmAndTurns()).toEqual(['summarize_data', 'summarize_data']);
    expect(screen.getByLabelText('Message')).toHaveValue('');
  });

  it('holds the plot button back while the box holds text over the cap: nothing confirms or goes', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(create);
    const long = 'a'.repeat(2001);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: long } });
    expect(create).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(create);
    expect(confirmAndTurns()).toEqual(['summarize_data']);
    expect(screen.getByLabelText('Message')).toHaveValue(long);
  });

  it('lets .update_plot() send the box text once the library has a plot, inert while the box is empty', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    const update = screen.getByRole('button', { name: 'Update plot' });
    expect(update).toHaveTextContent('.update_plot() →');
    expect(update).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(update);
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);

    // With text it sends the text as Enter does: a change of the latest version, no confirmation.
    fireEvent.change(screen.getByLabelText('Message'), {
      target: { value: 'what is the mean score?' },
    });
    expect(update).not.toHaveAttribute('aria-disabled');
    fireEvent.click(update);
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    expect(confirmAndTurns()).toEqual([
      'summarize_data',
      'confirm',
      'create_plot',
      'text: what is the mean score?',
    ]);
    expect(screen.getByLabelText('Message')).toHaveValue('');
    expect(update).toHaveAttribute('aria-disabled', 'true');
  });

  it('confirms and plots once for a double click', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    fireEvent.click(create);
    fireEvent.click(create);
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
  });

  it('names a required role without a column as what .create_plot() waits for', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
      if (new URL(input).pathname.endsWith('/sessions/S1/bindings') && init.method === 'PUT') {
        return json(200, {
          bindings: [{ role: 'x', column: 'hours' }],
          complete: false,
          missing_roles: ['y'],
        });
      }
      return base(input, init);
    });
    renderAt(PAGE);
    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    expect(create).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'step 1 of 2 · pick a column for y, then .create_plot()'
    );
    expect(create).toHaveAccessibleDescription(
      'step 1 of 2 · pick a column for y, then .create_plot()'
    );
  });
});

describe('AgentChatPage .plot_all()', () => {
  /** The fetch stub as `stubFetch` set it, for a test that answers one route differently. */
  const baseFetch = () =>
    fetchMock.getMockImplementation() as (input: string, init?: RequestInit) => Promise<Response>;
  const plotAllButton = () => screen.getByRole('button', { name: 'Plot in all libraries' });

  it('offers the fan-out once the lists are in, and .plot_all() confirms the table, then plots it everywhere', async () => {
    const base = baseFetch();
    // The catalogue's answer waits: until both lists are in, the libraries are fallbacks. The
    // status comes once, with the admin check, whose answer the chat takes over.
    let releaseSpec!: () => void;
    const spec = new Promise<void>(resolve => (releaseSpec = resolve));
    fetchMock.mockImplementation(async (input: string, init?: RequestInit) => {
      if (input.endsWith('/debug/agent/status')) {
        return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true, user_max_runs: 4 });
      }
      if (input.endsWith('/specs/scatter-basic')) await spec;
      return base(input, init);
    });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    let admin = await openAdminMenu();
    expect(within(admin).queryByRole('button', ALL_TOGGLE)).not.toBeInTheDocument();
    await closeAdminMenu();
    releaseSpec();

    admin = await openAdminMenu();
    const all = await within(admin).findByRole('button', ALL_TOGGLE);
    expect(all).toHaveTextContent(/^all 2 libraries$/);
    expect(all).toHaveAttribute('aria-pressed', 'false');
    await closeAdminMenu();
    // The library menu holds the libraries only, as a visitor's.
    let menu = await openLibraryMenu();
    expect(
      within(menu)
        .getAllByRole('button')
        .map(button => button.textContent)
    ).toEqual(['matplotlib', 'seaborn']);
    expect(within(menu).getByRole('button', { name: 'matplotlib' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    await closeLibraryMenu();
    expect(screen.queryByRole('button', { name: 'Plot in all libraries' })).not.toBeInTheDocument();

    // On, the fan-out is what the chip names, and the composer's create action plots everywhere.
    await toggleAll();
    expect(libraryChip()).toHaveTextContent(/^all 2 libraries ▾$/);
    expect(libraryChip()).toHaveAccessibleName('Library: all 2 libraries. Change');
    admin = await openAdminMenu();
    expect(within(admin).getByRole('button', ALL_TOGGLE)).toHaveAttribute('aria-pressed', 'true');
    await closeAdminMenu();
    menu = await openLibraryMenu();
    const own = within(menu).getByRole('button', { name: 'matplotlib' });
    expect(own).toHaveAttribute('aria-pressed', 'false');
    expect(own).toBeEnabled();
    await closeLibraryMenu();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    // In step 1 `.plot_all()` is the plot button, in its place; the chat about the data goes on.
    const plotAll = plotAllButton();
    expect(plotAll).toHaveTextContent('.plot_all()');
    expect(plotAll).not.toHaveAttribute('aria-disabled');
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.plot_all()']);
    // The line leads to the button that shows: `.plot_all()`, not the `.create_plot()` it replaces.
    expect(plotAll).toHaveAccessibleDescription(
      'step 1 of 2 · check the data and the bindings above, then .plot_all()'
    );
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.queryByTestId('plot-all-hint')).not.toBeInTheDocument();

    // The click confirms the data first: the copy route needs confirmed data.
    fireEvent.click(plotAll, { detail: 1 });
    const panel = await screen.findByRole('region', { name: 'All libraries' });
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm']);
    // The fan-out takes no text: in step 2 the message box waits, and the status line says why.
    const line =
      'step 2 of 2 · plot the table as it is in all 2 libraries at once · turn all off to chat';
    const box = screen.getByLabelText('Message');
    expect(box).toBeDisabled();
    expect(box).toHaveAccessibleDescription(line);
    expect(box).toHaveAttribute(
      'placeholder',
      'all libraries: the table goes as it is · turn all off to chat'
    );
    expect(plotAllButton()).toHaveAccessibleDescription(line);
    expect(
      within(panel)
        .getAllByRole('article')
        .map(card => card.getAttribute('aria-label'))
    ).toEqual(['matplotlib', 'seaborn']);
    expect(within(panel).getByText(/at most 4 at a time/)).toBeInTheDocument();
    // A pointer click moves no focus.
    expect(panel).not.toHaveFocus();
    // While the panel is open, nothing starts another fan-out or changes the library, whose
    // session the panel's sessions copy their data from; the fan-out stays on.
    expect(plotAllButton()).toHaveAttribute('aria-disabled', 'true');
    expect(libraryChip()).toBeDisabled();
    expect(libraryChip()).toHaveTextContent(/^all 2 libraries ▾$/);
    admin = await openAdminMenu();
    expect(within(admin).getByRole('button', ALL_TOGGLE)).toBeDisabled();
    await closeAdminMenu();

    // `.close()` goes with the panel: the focus returns to `.plot_all()`, which opened it.
    const close = within(panel).getByRole('button', { name: 'Close all libraries' });
    close.focus();
    fireEvent.click(close);
    expect(screen.queryByRole('region', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(plotAllButton()).not.toHaveAttribute('aria-disabled');
    expect(plotAllButton()).toHaveFocus();
    expect(libraryChip()).toBeEnabled();

    // A key press (a click with `detail` 0) continues in the panel it opened.
    fireEvent.click(plotAllButton(), { detail: 0 });
    expect(await screen.findByRole('region', { name: 'All libraries' })).toHaveFocus();
  });

  it('opens no panel when the confirmation .plot_all() starts with is refused', async () => {
    const base = baseFetch();
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) =>
      new URL(input).pathname.endsWith('/dataset/confirm')
        ? json(503, { detail: 'capacity', ref: 'r-a' })
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await toggleAll();
    const plotAll = plotAllButton();
    await untilActive(plotAll);

    fireEvent.click(plotAll, { detail: 1 });
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ref r-a'));
    // No panel, no copied session, and step 1 holds with `.plot_all()` ready for a retry.
    expect(screen.queryByRole('region', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm']);
    expect(agentCalls().some(([input]) => String(input).endsWith('/dataset/copy'))).toBe(false);
    expect(currentStep()).toBe(1);
    await untilActive(plotAllButton());
  });

  it('offers no fan-out when the page has one library', async () => {
    const base = baseFetch();
    fetchMock.mockImplementation((input: string, init?: RequestInit) =>
      input.endsWith('/debug/agent/status')
        ? Promise.resolve(json(200, { libraries: ['matplotlib'], enabled: true }))
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    const menu = await openLibraryMenu();
    await waitFor(() =>
      expect(within(menu).queryByRole('button', { name: 'seaborn' })).not.toBeInTheDocument()
    );
    await closeLibraryMenu();
    const admin = await openAdminMenu();
    expect(within(admin).queryByRole('button', ALL_TOGGLE)).not.toBeInTheDocument();
    expect(within(admin).getByRole('button', { name: 'Save' })).toBeInTheDocument();
    await closeAdminMenu();
    await untilActive(screen.getByRole('button', { name: 'Create plot' }));
  });

  it('turns the fan-out off from any library in the menu: the own one only that, another switches', async () => {
    const base = baseFetch();
    fetchMock.mockImplementation((input: string, init?: RequestInit) =>
      input.endsWith('/sessions/S1/library')
        ? Promise.resolve(
            json(200, {
              session_id: 'S1',
              eligibility: { eligible: true, status: 'clean', reasons: [] },
            })
          )
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });

    // The admin menu's toggle: a second click turns it off again.
    await toggleAll();
    expect(screen.getByLabelText('Message')).toBeDisabled();
    await toggleAll();
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);
    expect(screen.getByRole('button', { name: 'Start over' })).toHaveTextContent('.start_over()');
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).not.toHaveAccessibleDescription();

    await toggleAll();
    await pickInMenu('matplotlib');
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);
    // The menu closed and gave the focus back to its chip.
    await waitFor(() => expect(libraryChip()).toHaveFocus());
    const menu = await openLibraryMenu();
    const own = within(menu).getByRole('button', { name: 'matplotlib' });
    expect(own).toHaveAttribute('aria-pressed', 'true');
    expect(own).toBeDisabled();
    await closeLibraryMenu();
    expect(screen.getByRole('button', { name: 'Start over' })).toHaveTextContent('.start_over()');
    // The draft waited in the box, and nothing switched.
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).toHaveValue('log scale on y');
    expect(agentCalls().filter(([input]) => String(input).endsWith('/library'))).toEqual([]);

    await toggleAll();
    await pickInMenu('seaborn');
    await waitFor(() =>
      expect(screen.getByTestId('location')).toHaveTextContent('library=seaborn')
    );
    expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/);
  });

  it('leaves the chat about the data usable with the fan-out on, before data and in step 1', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    // Without data: nothing to plot yet, `.plot_all()` stands quiet and inert in the plot
    // button's place, and the box asks for a curve as without the fan-out.
    await toggleAll();
    expect(libraryChip()).toHaveTextContent(/^all \d+ libraries ▾$/);
    expect(composerButtons()).toEqual(['.example_data()', '.plot_all() (inert)']);
    const box = screen.getByLabelText('Message');
    expect(box).toBeEnabled();
    expect(box).toHaveAttribute('placeholder', 'paste a table or drop a file');
    expect(box).not.toHaveAccessibleDescription();

    // Step 1: `.plot_all()` is the action, and a question about the data goes: the box waits
    // only once the data is confirmed.
    await parseAndSummarize();
    expect(currentStep()).toBe(1);
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.plot_all()']);
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the first plot should do'
    );
    sendFromComposer('what is the mean score?');
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ text: 'what is the mean score?' });
    expect(libraryChip()).toHaveTextContent(/^all \d+ libraries ▾$/);
    expect(confirmAndTurns()).toEqual(['summarize_data', 'text: what is the mean score?']);
  });

  it('lets an attachment go with Enter while the fan-out holds the box in step 2, note and all', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    await toggleAll();
    const box = screen.getByLabelText('Message');
    expect(box).toBeDisabled();

    // New data goes all the same: the box opens for Enter and a note, since on a desktop no `↵`
    // shows and no `.send()` stands beside it.
    fireEvent.paste(box, {
      clipboardData: { files: [], getData: () => 'hours,score\n3,70\n4,80\n' },
    });
    await screen.findByRole('group', { name: /^Attached/ });
    expect(box).toBeEnabled();
    expect(box).toBeVisible();
    fireEvent.change(box, { target: { value: 'what is the mean score?' } });
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    const posts = agentCalls().filter(
      ([input, init]) =>
        pathOf(input).endsWith('/dataset') && (init as RequestInit | undefined)?.method === 'POST'
    );
    expect(posts).toHaveLength(2);
    expect(lastTurn()).toEqual({ text: 'what is the mean score?' });
  });

  /**
   * The fan-out's sessions under ids of their own (`F-<library>`): `copy` answers their copy route,
   * and each one's `create_plot` ships a plot.
   */
  function fanOutSessions(copy: () => Response) {
    const base = baseFetch();
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
      const path = new URL(input).pathname;
      const method = init.method ?? 'GET';
      const body = typeof init.body === 'string' ? JSON.parse(init.body) : {};
      if (path.endsWith('/debug/agent/sessions') && method === 'POST' && body.source === 'fanout') {
        return json(200, {
          session_id: `F-${body.library}`,
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      const fanned = path.match(/\/sessions\/(F-[a-z0-9]+)(\/.*)?$/);
      if (!fanned) return base(input, init);
      const rest = fanned[2] ?? '';
      if (method === 'DELETE') return new Response(null, { status: 204 });
      if (rest === '/dataset/copy') return copy();
      if (rest === '/dataset') return json(200, DATASET);
      if (rest === '/bindings')
        return json(200, { bindings: body, complete: true, missing_roles: [] });
      if (rest === '/dataset/confirm') return json(200, { confirmed: true, rows: 2, columns: 2 });
      if (rest === '/messages') return sse(turnEvents(body));
      return json(404, { detail: 'not_found' });
    });
  }
  const fanOutCalls = (rest: string) =>
    agentCalls()
      .filter(([input]) => /\/sessions\/F-[a-z0-9]+/.test(String(input)))
      .filter(([input]) => pathOf(input).endsWith(rest))
      .map(([input, init]) => ({
        session: String(input).match(/F-[a-z0-9]+/)?.[0],
        body: (init as RequestInit).body ? JSON.parse(String((init as RequestInit).body)) : null,
      }));

  it('plots data the assistant computed: the fan-out has the server copy it', async () => {
    fanOutSessions(() =>
      json(200, {
        ...GENERATED,
        confirmed: true,
        complete: true,
        missing_roles: [],
        copied_from: 1,
      })
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    sendFromComposer('y = sin(x), x from -pi to pi');
    expect(await screen.findByText('I generated 200 rows from y = sin(x).')).toBeInTheDocument();
    await turnEnded();

    await toggleAll();
    // Computed data has no paste, and `.plot_all()` needs none: it is the action, with no hint.
    const plotAll = plotAllButton();
    await untilActive(plotAll);
    expect(screen.queryByTestId('plot-all-hint')).not.toBeInTheDocument();
    fireEvent.click(plotAll, { detail: 1 });

    const panel = await screen.findByRole('region', { name: 'All libraries' });
    // The computed data was confirmed by the same click.
    expect(currentStep()).toBe(2);
    await waitFor(() => expect(fanOutCalls('/messages')).toHaveLength(2));
    expect(fanOutCalls('/dataset/copy')).toEqual([
      { session: 'F-matplotlib', body: { from_session: 'S1' } },
      { session: 'F-seaborn', body: { from_session: 'S1' } },
    ]);
    expect(fanOutCalls('/dataset')).toEqual([]);
    await waitFor(() =>
      expect(
        within(panel)
          .getAllByTestId('fanout-status')
          .map(line => line.textContent)
      ).toEqual(['matplotlib: v1 · ok', 'seaborn: v1 · ok'])
    );
  });

  it('locks the data card while the panel copies the data, and frees it on .close()', async () => {
    fanOutSessions(() =>
      json(200, { ...DATASET, confirmed: true, complete: true, missing_roles: [], copied_from: 1 })
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await toggleAll();
    fireEvent.click(plotAllButton(), { detail: 1 });
    const panel = await screen.findByRole('region', { name: 'All libraries' });

    // The card stays open, but nothing in it changes the data.
    const card = screen.getByRole('region', { name: 'Your data' });
    const line = '# the data waits while all libraries plot it · .close() the panel to change it';
    expect(within(card).getByTestId('data-lock')).toHaveTextContent(line);
    expect(card).toHaveAccessibleDescription(line);
    openBindings();
    expect(within(card).getByLabelText(/^x/)).toBeDisabled();
    // A new file waits too: the panel's sessions copy this data.
    expect(screen.getByRole('button', { name: 'Open a data file' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );

    fireEvent.click(within(panel).getByRole('button', { name: 'Close all libraries' }));
    expect(screen.queryByTestId('data-lock')).not.toBeInTheDocument();
    const reopened = screen.getByRole('region', { name: 'Your data' });
    expect(reopened).not.toHaveAccessibleDescription();
    expect(screen.getByRole('button', { name: 'Open a data file' })).not.toHaveAttribute(
      'aria-disabled'
    );
    expect(within(reopened).getByLabelText(/^x/)).toBeEnabled();
  });

  it('posts the paste again in every library while the server has no copy', async () => {
    fanOutSessions(() => json(404, { detail: 'not_found', ref: 'r-404' }));
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await toggleAll();
    fireEvent.click(plotAllButton(), { detail: 1 });

    await waitFor(() => expect(fanOutCalls('/messages')).toHaveLength(2));
    expect(fanOutCalls('/dataset').map(call => call.body)).toEqual([
      { text: 'hours,score\n1.5,52\n2.0,58\n' },
      { text: 'hours,score\n1.5,52\n2.0,58\n' },
    ]);
    expect(fanOutCalls('/bindings').map(call => call.body)).toEqual([
      DATASET.bindings,
      DATASET.bindings,
    ]);
  });
});

describe('AgentChatPage URL', () => {
  const location = () => screen.getByTestId('location').textContent ?? '';
  const query = () => new URLSearchParams(location().split('?')[1]);

  /** The page's libraries with one of another language, and a library switch the server takes. */
  function threeLibraries(statusGate?: Promise<void>) {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation(async (input: string, init?: RequestInit) => {
      const path = new URL(input).pathname;
      if (path.endsWith('/debug/agent/status')) {
        await statusGate;
        return json(200, { libraries: ['matplotlib', 'seaborn', 'ggplot2'], enabled: true });
      }
      if (path.endsWith('/specs/scatter-basic')) {
        return json(200, {
          title: 'Basic Scatter Plot',
          implementations: ['matplotlib', 'seaborn', 'ggplot2'].map(library_id => ({ library_id })),
        });
      }
      if (path.endsWith('/sessions/S1/library')) {
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      return base(input, init);
    });
  }

  it('writes the language of the library it switches to', async () => {
    threeLibraries();
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt('/agent?spec=scatter-basic&library=matplotlib&language=javascript');
    // The header moves into the chat column once the session is open: look for the menu there.
    await screen.findByLabelText('Message');
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);

    await pickInMenu('ggplot2');
    await waitFor(() => expect(query().get('library')).toBe('ggplot2'));
    expect(query().get('language')).toBe('r');
    expect(libraryChip()).toHaveTextContent(/^ggplot2 ▾$/);
    expect(libraryChip()).toHaveAccessibleName('Library: ggplot2, R. Change');

    await pickInMenu('seaborn');
    await waitFor(() => expect(query().get('library')).toBe('seaborn'));
    expect(query().get('language')).toBe('python');
    expect(query().get('spec')).toBe('scatter-basic');
  });

  it('keeps the fan-out out of the URL: the old &all=1 presses nothing, a toggle writes nothing', async () => {
    threeLibraries();
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&all=1`);
    await screen.findByLabelText('Message');
    await waitFor(() => expect(libraryChip()).toBeEnabled());
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);

    await toggleAll();
    await waitFor(() => expect(libraryChip()).toHaveTextContent(/^all 3 libraries ▾$/));
    const menu = await openAdminMenu();
    expect(within(menu).getByRole('button', ALL_TOGGLE)).toHaveAttribute('aria-pressed', 'true');
    await closeAdminMenu();

    // Another library switches and turns the fan-out off: the URL names the new library.
    await pickInMenu('seaborn');
    await waitFor(() => expect(query().get('library')).toBe('seaborn'));
    expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/);
    expect(query().get('spec')).toBe('scatter-basic');
  });
});

describe('AgentChatPage load mood and admin meters', () => {
  /**
   * The status answers as `stubFetch` gives them, plus `extra`, the next ones from `later` in
   * turn (the last one stays), and the day budget for the admin meters.
   */
  function statusWith(extra: Record<string, unknown>, ...later: Record<string, unknown>[]) {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    const answers = [extra, ...later];
    fetchMock.mockImplementation((input: string, init?: RequestInit) => {
      if (input.endsWith('/debug/agent/status')) {
        const next = answers.length > 1 ? answers.shift()! : answers[0];
        return Promise.resolve(
          json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true, ...next })
        );
      }
      if (input.endsWith('/debug/agent/budget')) {
        return Promise.resolve(
          json(200, {
            since: '2026-11-09T00:00:00Z',
            started_at: '2026-11-09T00:00:00Z',
            resets_at: '2026-11-10T00:00:00Z',
            paused: false,
            tokens: 620_000,
            budget_tokens: 1_000_000,
          })
        );
      }
      return base(input, init);
    });
  }
  const mood = () => screen.getByTestId('load-mood');
  const statusCalls = () =>
    agentCalls().filter(([input]) => pathOf(input) === '/debug/agent/status').length;
  const budgetCalls = () =>
    fetchMock.mock.calls.filter(([input]) => String(input).includes('/budget')).length;

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('shows the mood on the tab after the path, a status of its own: quiet, busy, resting', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    statusWith({ waiting: 0 });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const quiet = renderAt(PAGE);
    await waitFor(() => expect(mood()).toHaveTextContent(/^· ● the assistant is quiet$/));
    expect(mood()).toHaveAttribute('role', 'status');
    expect(mood().closest('[aria-hidden="true"]')).toBeNull();
    expect(screen.getByTestId('chat-frame-tab')).toHaveAttribute('aria-hidden', 'true');
    quiet.unmount();

    statusWith({ waiting: 2 });
    const busy = renderAt(PAGE);
    await waitFor(() => expect(mood()).toHaveTextContent(/busy$/));
    busy.unmount();

    // The day budget spent: resting until the reset in the visitor's own time. The pause note
    // above the composer is gone; the composer stays, since the server decides each turn.
    const resetsAt = new Date(Date.now() + 3_600_000).toISOString();
    statusWith({ paused: true, resets_at: resetsAt });
    renderAt(PAGE);
    await waitFor(() =>
      expect(mood()).toHaveTextContent(new RegExp(`resting until ${localClock(resetsAt)}$`))
    );
    expect(screen.queryByTestId('service-paused')).not.toBeInTheDocument();
    expect(screen.queryByText(/today's overall limit/)).not.toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toBeInTheDocument();
    // The pause ends at the reset, without a reload (and without a read: the tab is hidden).
    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden');
    await act(async () => vi.advanceTimersByTimeAsync(3_600_000));
    await waitFor(() => expect(mood()).toHaveTextContent(/quiet$/));
  });

  it('reads again every 60 s while visible, keeps the libraries, and stops when the page goes', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible');
    statusWith({ waiting: 0 }, { waiting: 3, libraries: ['matplotlib'] });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { unmount } = renderAt(PAGE);
    await waitFor(() => expect(mood()).toHaveTextContent(/quiet$/));
    expect(statusCalls()).toBe(1);
    await act(async () => vi.advanceTimersByTimeAsync(60_000));
    await waitFor(() => expect(mood()).toHaveTextContent(/busy$/));
    expect(statusCalls()).toBe(2);
    // A poll changes the load only: the fan-out still counts the first read's libraries.
    const menu = await openAdminMenu();
    expect(within(menu).getByRole('button', ALL_TOGGLE)).toHaveTextContent('all 2 libraries');
    await closeAdminMenu();
    const before = statusCalls();
    unmount();
    await act(async () => vi.advanceTimersByTimeAsync(5 * 60_000));
    expect(statusCalls()).toBe(before);
  });

  it('turns resting at once on a service_paused refusal', async () => {
    statusWith({ waiting: 0 });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await waitFor(() => expect(mood()).toHaveTextContent(/quiet$/));
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    // The refusal arrives, and the turn's `done` waits: no read can have brought the pause yet.
    let finish: (() => void) | null = null;
    const refused = () =>
      new Response(
        new ReadableStream({
          start(controller) {
            const write = (list: [string, unknown][]) =>
              controller.enqueue(
                new TextEncoder().encode(
                  list
                    .map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
                    .join('')
                )
              );
            write([
              ['refusal', { code: 'service_paused', text: 'paused for today, until 00:00 UTC' }],
            ]);
            finish = () => {
              write([['done', {}]]);
              controller.close();
            };
          },
        }),
        { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
      );
    fetchMock.mockImplementation((input: string, init: RequestInit = {}) =>
      pathOf(input).endsWith('/sessions/S1/messages')
        ? Promise.resolve(refused())
        : base(input, init)
    );
    const box = await screen.findByLabelText('Message');
    await waitFor(() => expect(box).toBeEnabled());
    const reads = statusCalls();
    sendFromComposer('hello');
    await screen.findByTestId('refusal');
    // The refusal names the next 00:00 UTC; the tab says it in the user's time, before any read.
    await waitFor(() =>
      expect(mood()).toHaveTextContent(
        new RegExp(`resting until ${localClock(nextUtcMidnight())}$`)
      )
    );
    expect(statusCalls()).toBe(reads);
    act(() => finish?.());
    await turnEnded();
  });

  it('reads the meters as the admin menu opens during a run, and leaves the tab as it was', async () => {
    statusWith({ waiting: 0, in_flight: 1 });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await waitFor(() => expect(mood()).toHaveTextContent(/quiet$/));
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    await screen.findByTestId('working-line');
    const statusBefore = statusCalls();
    expect(budgetCalls()).toBe(0);

    // Meanwhile the queue filled up and more runs are in flight.
    statusWith({ waiting: 4, in_flight: 3 });
    const menu = await openAdminMenu();
    // One `/status` through the one reader, and one `/budget`.
    await waitFor(() =>
      expect(within(menu).getByTestId('admin-meters')).toHaveTextContent(
        /^now 3 runs · today 62 %$/
      )
    );
    expect(statusCalls()).toBe(statusBefore + 1);
    expect(budgetCalls()).toBe(1);
    // The menu's answer during the run feeds the meters alone: the tab shows what a visitor's does.
    expect(mood()).toHaveTextContent(/quiet$/);
    await closeAdminMenu();
    releaseTurn?.();
    await turnEnded();
  });
});

describe('AgentChatPage library switch and plot memory', () => {
  const LINE: MemoryEntry = {
    id: 'm1',
    kind: 'reference_line',
    target: 'y',
    text: 'horizontal reference line at y = 7',
    expect: null,
    turn: 2,
  };
  const LABEL: MemoryEntry = {
    id: 'm2',
    kind: 'axis_label',
    target: 'x',
    text: "x-axis label: 'Zeit (h)'",
    expect: 'Zeit (h)',
    turn: 2,
  };
  const OFFER = { decisions: 2, newer: 2, target_has_plot: false, from_plot: true, offer: true };

  /**
   * The routes of the switch, the plot memory and a plot per run (the next version each): `carry`
   * answers each switch; `memory` lists the entries, which a DELETE removes; `holdNextTurn` keeps
   * the next turn's stream until `releaseTurn`.
   */
  function switchRoutes(state: {
    carry: unknown;
    memory: MemoryEntry[];
    libraryStatus?: number;
    /** `done.switch` of a typed turn: the switch the assistant's `switch_plot` asked for. */
    chatSwitch?: { library: string; plot: boolean };
  }) {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    let version = 0;
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
      const path = new URL(input).pathname;
      const method = init.method ?? 'GET';
      if (path.endsWith('/sessions/S1/library')) {
        if (state.libraryStatus) {
          return json(state.libraryStatus, { detail: 'not_eligible', ref: 'r-sw' });
        }
        const { library } = JSON.parse(String(init.body)) as { library: string };
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
          target: { spec_id: 'scatter-basic', library },
          carry: state.carry,
        });
      }
      if (path.endsWith('/sessions/S1/memory') && method === 'GET') {
        return json(200, { entries: state.memory, max_entries: 30 });
      }
      const forget = path.match(/\/sessions\/S1\/memory\/(m\d+)$/);
      if (forget && method === 'DELETE') {
        state.memory = state.memory.filter(item => item.id !== forget[1]);
        return json(200, { entries: state.memory, max_entries: 30 });
      }
      if (path.endsWith('/sessions/S1/messages') && method === 'POST') {
        const body = JSON.parse(String(init.body)) as { action?: string; text?: string };
        if (body.action === 'summarize_data') return base(input, init);
        if (body.text && state.chatSwitch) {
          // The assistant asked for the switch and ran no plot: the page carries it out.
          return sse([
            ['message', { text: 'The plot comes in seaborn with your decisions.' }],
            ['done', { llm_calls: 2, data_confirmed: true, switch: state.chatSwitch }],
          ]);
        }
        version += 1;
        const response = sse([
          ['plot', { ...PLOT, version }],
          ['message', { text: `Plot ${version}.` }],
          ['done', { llm_calls: 2, data_confirmed: true }],
        ]);
        if (!holdNextTurn) return response;
        holdNextTurn = false;
        return new Promise<Response>(resolve => {
          releaseTurn = () => resolve(response);
        });
      }
      return base(input, init);
    });
  }

  /** The remembered decisions' count on the latest `# plot` line, which unfolds their list. */
  const decisionsCount = (count: string) =>
    screen.findByRole('button', { name: `${count} remembered` });
  const memoryList = () => screen.getByRole('list', { name: 'Remembered decisions' });

  /** Paste and plot in matplotlib with one click: version 1, whose run left `memory` behind. */
  async function plotInMatplotlib() {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Plot 1.')).toBeInTheDocument();
    await turnEnded();
  }

  it('offers the plot in the new library with the remembered decisions, and the offer ends once it ships', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    // The run's decisions stand on the `# plot` line, their list folded under it.
    const count = await decisionsCount('2 decisions');
    expect(count.closest('[data-testid="chapter-line"]')).toHaveAttribute('data-chapter', 'plot');
    expect(count).toHaveAttribute('aria-expanded', 'false');
    const turns = turnBodies().length;

    const create = screen.getByRole('button', { name: 'Update plot' });
    await pickInMenu('seaborn');
    // Browsing costs nothing: the switch runs no turn.
    await waitFor(() =>
      expect(screen.getByTestId('data-step')).toHaveTextContent(
        /^>>> step 2 of 2 · 2 decisions kept in seaborn · /
      )
    );
    expect(turnBodies()).toHaveLength(turns);
    // Seaborn has no plot yet: the plot button keeps its place and its name, and the status
    // line, its description, names the decisions its click takes along.
    expect(screen.getByRole('button', { name: 'Create plot' })).toBe(create);
    expect(screen.queryByTestId('carry-plot')).not.toBeInTheDocument();
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
    expect(create).toHaveAccessibleDescription(
      'step 2 of 2 · 2 decisions kept in seaborn · create the plot as it is, or say first what it should do differently'
    );
    // The plot from the catalogue code without the carry, `.start_over()`, waits at the status
    // line's end.
    expect(statusActions()).toEqual(['.start_over()']);
    const fresh = screen.getByRole('button', { name: 'Start over' });
    expect(fresh).toHaveAccessibleDescription(
      expect.stringContaining('keeps your remembered decisions')
    );

    fireEvent.click(create, { detail: 1 });
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ action: 'carry_plot' });
    const thread = screen.getByRole('log', { name: 'Conversation' });
    // The thread names the button as it read, and the library, never the action the page sent.
    expect(lastAction()).toHaveTextContent(/^❯\.create_plot\(\)# seaborn$/);
    expect(within(thread).queryByText(/carry_plot/)).not.toBeInTheDocument();
    // Shipped in seaborn: the offer is spent, the plot button updates this plot.
    expect(screen.getByTestId('data-step')).not.toHaveTextContent('decisions kept');
    expect(screen.getByRole('button', { name: 'Start over' })).not.toHaveAttribute('aria-disabled');
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.update_plot() → (inert)']);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'a title' } });
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.update_plot() →']);
  });

  it('confirms changed data before the carry, in the same click', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await waitFor(() =>
      expect(screen.getByTestId('data-step')).toHaveTextContent('2 decisions kept in seaborn')
    );
    // A binding changed in the new library drops the confirmation the switch kept.
    openBindings();
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });
    await waitFor(() => expect(currentStep()).toBe(1));
    const carry = screen.getByRole('button', { name: 'Create plot' });
    await untilActive(carry);
    const before = confirmAndTurns().length;

    fireEvent.click(carry);
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    expect(confirmAndTurns().slice(before)).toEqual(['confirm', 'carry_plot']);
  });

  it('carries out a switch asked for in the chat and plots there without a second click', async () => {
    switchRoutes({
      carry: OFFER,
      memory: [LINE, LABEL],
      chatSwitch: { library: 'seaborn', plot: true },
    });
    await plotInMatplotlib();

    fireEvent.change(screen.getByRole('textbox', { name: 'Message' }), {
      target: { value: 'mach den Plot bitte in seaborn' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Update plot' }));

    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    const switches = fetchMock.mock.calls.filter(([input]) =>
      String(input).endsWith('/sessions/S1/library')
    );
    expect(switches).toHaveLength(1);
    expect(JSON.parse(String((switches[0][1] as RequestInit).body))).toEqual({
      spec_id: 'scatter-basic',
      library: 'seaborn',
      source: 'chat',
    });
    expect(lastTurn()).toEqual({ action: 'carry_plot' });
    expect(screen.getByRole('button', { name: /^Library: seaborn/ })).toBeInTheDocument();
  });

  it('shows a switch the server refused in the thread, and plots nothing', async () => {
    switchRoutes({
      carry: OFFER,
      memory: [],
      libraryStatus: 422,
      chatSwitch: { library: 'seaborn', plot: true },
    });
    await plotInMatplotlib();
    const turns = turnBodies().length;

    sendFromComposer('make it in seaborn');

    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(
      await within(thread).findByText(/this plot cannot be adapted in that library/)
    ).not.toHaveTextContent('r-sw');
    await turnEnded();
    expect(turnBodies()).toHaveLength(turns + 1); // the typed turn alone: no carry run
  });

  it('sends .start_over() after a switch as the fresh plot, which ends the offer too', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await waitFor(() => expect(statusActions()).toEqual(['.start_over()']));
    fireEvent.click(screen.getByRole('button', { name: 'Start over' }));
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ action: 'create_plot' });
    expect(screen.getByTestId('data-step')).not.toHaveTextContent('decisions kept');
  });

  it('names no decisions after a switch whose offer carries none, and carries with the plot button', async () => {
    // With nothing to take along, the line names nothing and no `.start_over()` waits.
    switchRoutes({
      carry: { decisions: 0, newer: 0, target_has_plot: false, from_plot: true, offer: true },
      memory: [],
    });
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await waitFor(() => expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/));
    expect(composerButtons()).toEqual(['.example_data() (inert)', '.create_plot() →']);
    expect(statusActions()).toEqual([]);
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · create the plot as it is, or say first/
    );

    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    // The carry still runs, with the theme asked for in the library before.
    expect(lastTurn()).toEqual({ action: 'carry_plot' });
  });

  it('lets .update_plot() bring newer decisions into a library with an older plot; text goes as a turn', async () => {
    const routes = { carry: OFFER as unknown, memory: [LINE] };
    switchRoutes(routes);
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await waitFor(() =>
      expect(screen.getByTestId('data-step')).toHaveTextContent('1 decision kept in seaborn')
    );
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();

    // Back to matplotlib, whose plot misses a newer decision: the server offers the carry again,
    // and `.update_plot() →` acts with an empty box, the status line saying what it brings.
    routes.carry = { decisions: 1, newer: 1, target_has_plot: true, from_plot: true, offer: true };
    await pickInMenu('matplotlib');
    await waitFor(() =>
      expect(screen.getByTestId('data-step')).toHaveTextContent(
        /^>>> step 2 of 2 · 1 decision kept in matplotlib · \.update_plot\(\) brings them in, or ask for a change$/
      )
    );
    const update = screen.getByRole('button', { name: 'Update plot' });
    expect(update).not.toHaveAttribute('aria-disabled');
    expect(statusActions()).toEqual(['.start_over()']);
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();

    // Text in the box goes as a turn, which the server also gives the decisions.
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'dashed line' } });
    fireEvent.click(update);
    expect(await screen.findByText('Plot 3.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ text: 'dashed line' });
    // The typed change shipped in matplotlib: that ends the offer as well.
    expect(screen.getByTestId('data-step')).not.toHaveTextContent('decisions kept');
    expect(update).toHaveAttribute('aria-disabled', 'true');
  });

  it('offers nothing after a switch whose answer has no offer', async () => {
    switchRoutes({
      carry: { decisions: 0, newer: 0, target_has_plot: false, from_plot: false, offer: false },
      memory: [],
    });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await pickInMenu('seaborn');
    await waitFor(() => expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/));
    expect(screen.getByTestId('data-step')).not.toHaveTextContent('decisions kept');
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveTextContent('.create_plot()');
    expect(screen.queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    expect(screen.queryByRole('list', { name: 'Remembered decisions' })).not.toBeInTheDocument();
  });

  it('forgets a remembered decision, and holds the list while a turn runs', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    fireEvent.click(await decisionsCount('2 decisions'));
    const list = memoryList();
    const forgetLine = within(list).getByRole('button', { name: `Forget: ${LINE.text}` });

    // While a turn runs, the server would refuse a removal: the list waits.
    holdNextTurn = true;
    sendFromComposer('thicker markers');
    await waitFor(() => expect(releaseTurn).not.toBeNull());
    expect(forgetLine).toBeDisabled();
    releaseTurn?.();
    await turnEnded();

    await waitFor(() => expect(forgetLine).toBeEnabled());
    fireEvent.click(forgetLine);
    // The plot turn opened no newer `# plot` chapter: the count stays on its line, one less.
    expect(await decisionsCount('1 decision')).toHaveAttribute('aria-expanded', 'true');
    expect(
      agentCalls()
        .filter(([, init]) => (init as RequestInit | undefined)?.method === 'DELETE')
        .map(([input]) => pathOf(input))
    ).toContain('/debug/agent/sessions/S1/memory/m1');
    expect(within(memoryList()).queryByText(LINE.text)).not.toBeInTheDocument();
    expect(within(memoryList()).getByText(LABEL.text)).toBeInTheDocument();
    // Said outside the thread's log, by the region at the chat's foot, which stays.
    const status = screen.getByTestId('memory-status');
    expect(status).toHaveTextContent(`forgot: ${LINE.text}`);
    expect(screen.getByRole('log', { name: 'Conversation' })).not.toContainElement(status);
  });

  it('shows a refused switch under the menu, and the library and the URL stay', async () => {
    switchRoutes({ carry: OFFER, memory: [], libraryStatus: 422 });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await pickInMenu('seaborn');
    expect(await screen.findByRole('alert')).toHaveTextContent(
      /^could not switch: this plot cannot be adapted in that library$/
    );
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);
    expect(screen.getByTestId('location')).toHaveTextContent('library=matplotlib');
    // Said where the user picked, not again in the thread.
    expect(
      within(screen.getByRole('log', { name: 'Conversation' })).queryByText(/error ·/)
    ).not.toBeInTheDocument();
  });
});

describe('AgentChatPage attachment', () => {
  const TABLE = 'hours,score\n1.5,52\n2.0,58\n3.0,61\n';
  const message = () => screen.getByLabelText('Message');
  const chip = () => screen.getByRole('group', { name: /^Attached/ });
  const datasetPosts = () =>
    agentCalls().filter(
      ([input, init]) =>
        pathOf(input).endsWith('/dataset') && (init as RequestInit | undefined)?.method === 'POST'
    );
  /** A paste into the message box; the event says whether the browser would paste it. */
  const pasteText = (text: string) =>
    fireEvent.paste(message(), { clipboardData: { files: [], getData: () => text } });
  /** Answers the dataset route's calls with `answer` before the rest of the stub. */
  function routeDataset(answer: (path: string, init: RequestInit) => Response | undefined) {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
      const path = new URL(input).pathname;
      return (path.includes('/dataset') && answer(path, init)) || base(input, init);
    });
  }
  async function openChat() {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    await waitFor(() => expect(message()).toBeEnabled());
  }

  it('attaches a pasted table as a chip, keeps prose a paste, and names the chip to a screen reader', async () => {
    await openChat();
    // Prose: the browser's own paste goes ahead (the event is not cancelled).
    expect(pasteText('Make the bars blue\nand add a grid')).toBe(true);
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();

    // A table: no text in the box, a chip with its size, Enter (or the `↵` on a touch screen)
    // to read it, the plot button to read and plot it; example data waits, since the table is
    // data at hand.
    expect(pasteText(TABLE)).toBe(false);
    expect(message()).toHaveValue('');
    expect(chip()).toHaveAccessibleName('Attached table, 4 lines, 33 B');
    expect(chip()).toHaveTextContent('▤ table · 4 lines · 33 B');
    expect(screen.getByTestId('composer-status')).toHaveTextContent('Attached table, 4 lines');
    expect(composerButtons()).toEqual(['.example_data() (inert)', '×', '.create_plot() →']);
    expect(screen.getByTestId('send-return')).not.toHaveAttribute('aria-disabled');
    expect(message()).toHaveAttribute('placeholder', 'add a note for this table, or press Enter');
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'step 1 of 2 · .create_plot() reads the attached table and plots it · Enter ↵ only reads it'
    );
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_input_routed', {
      as: 'data',
      via: 'paste',
    });
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_input_routed', {
      as: 'message',
      via: 'paste',
    });
  });

  it('attaches a copied web table with grouped columns from its HTML, the spans expanded', async () => {
    await openChat();
    const plain = 'Place\tArea\nkm2\tmi2\nOrt A\t10\t3.9\nOrt B\t20\t7.7\n';
    const html =
      '<table><tr><th rowspan="2">Place</th><th colspan="2">Area</th></tr><tr><th>km2</th><th>mi2</th></tr>' +
      '<tr><td>Ort A</td><td>10</td><td>3.9</td></tr><tr><td>Ort B</td><td>20</td><td>7.7</td></tr></table>';
    const getData = (type: string) => (type === 'text/html' ? html : plain);
    expect(fireEvent.paste(message(), { clipboardData: { files: [], getData } })).toBe(false);
    fireEvent.keyDown(message(), { key: 'Enter' });

    await waitFor(() => expect(datasetPosts()).toHaveLength(1));
    const body = JSON.parse(String((datasetPosts()[0][1] as RequestInit).body)) as { text: string };
    expect(body.text).toBe('Place\tArea\tArea\nPlace\tkm2\tmi2\nOrt A\t10\t3.9\nOrt B\t20\t7.7\n');
  });

  it('reads the chip on Enter with the summary first when no note came with it', async () => {
    await openChat();
    pasteText(TABLE);
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    expect(String((datasetPosts()[0][1] as RequestInit).body)).toContain('hours,score');
    expect(turnBodies()).toEqual([{ action: 'summarize_data' }]);
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
  });

  it('sends the typed text as the first turn after the data, in place of the summary', async () => {
    await openChat();
    pasteText(TABLE);
    fireEvent.change(message(), { target: { value: 'what is the mean score?' } });
    // The `↵` a touch screen shows in the box sends as Enter does.
    fireEvent.click(screen.getByTestId('send-return'));
    // The note left the box at once, and it is the user's line in the thread.
    expect(message()).toHaveValue('');
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    expect(turnBodies()).toEqual([{ text: 'what is the mean score?' }]);
    expect(
      within(screen.getByRole('log', { name: 'Conversation' })).getByText('what is the mean score?')
    ).toBeInTheDocument();
  });

  it('keeps a refused table red with the reason, and puts the note back before newer text', async () => {
    routeDataset(path =>
      path.endsWith('/dataset')
        ? json(422, { detail: 'unparseable', cause: 'the rows have different lengths', ref: 'r-u' })
        : undefined
    );
    await openChat();
    pasteText(TABLE);
    fireEvent.change(message(), { target: { value: 'only 2024' } });
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(await screen.findByTestId('attachment-error')).toHaveTextContent(
      /^the rows have different lengths$/
    );
    expect(chip()).toHaveAttribute('data-status', 'failed');
    await waitFor(() => expect(message()).toHaveValue('only 2024'));
    expect(turnBodies()).toEqual([]);
    // Enter, or the `↵` on a touch screen, tries the same table again.
    expect(screen.getByTestId('send-return')).not.toHaveAttribute('aria-disabled');
  });

  it('reads a table typed into the box as data on Enter, and keeps typed prose a message', async () => {
    await openChat();
    // Prose over two lines, commas and all, is what the user meant to say.
    sendFromComposer('make the bars blue, add a grid,\nand sort them by value');
    await turnEnded();
    expect(turnBodies()).toEqual([
      { text: 'make the bars blue, add a grid,\nand sort them by value' },
    ]);
    expect(datasetPosts()).toHaveLength(0);

    // A table typed by hand, as no paste event saw it: the dataset route reads it, with no note,
    // and the summary is the turn on it, as after a paste.
    sendFromComposer(TABLE);
    expect(message()).toHaveValue('');
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    const posted = datasetPosts().map(([, init]) => JSON.parse(String((init as RequestInit).body)));
    expect(posted).toEqual([expect.objectContaining({ text: TABLE.trim() })]);
    expect(turnBodies().slice(1)).toEqual([{ action: 'summarize_data' }]);
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_input_routed', {
      as: 'data',
      via: 'typed',
    });
  });

  it('keeps a refused typed table red, and × puts it back into the box', async () => {
    routeDataset(path =>
      path.endsWith('/dataset')
        ? json(422, { detail: 'unparseable', cause: 'the rows have different lengths', ref: 'r-u' })
        : undefined
    );
    await openChat();
    sendFromComposer(TABLE);
    expect(await screen.findByTestId('attachment-error')).toHaveTextContent(
      /^the rows have different lengths$/
    );
    expect(message()).toHaveValue('');
    // Nothing else holds the typed text: × gives it back to edit.
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    expect(message()).toHaveValue(TABLE.trim());
    expect(turnBodies()).toEqual([]);
  });

  it('lets a table read from text go from the chip and the note back into the box', async () => {
    await openChat();
    // Long text over the chat limit always attaches; the stub reads `Hund` as free text.
    pasteText(`${FREE_TEXT}\n${'Pferd 1 Esel 5\n'.repeat(140)}`);
    fireEvent.change(message(), { target: { value: 'the animals of 2024' } });
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(await screen.findByTestId('transcription-card')).toBeInTheDocument();
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    await waitFor(() => expect(message()).toHaveValue('the animals of 2024'));
    expect(turnBodies()).toEqual([]);
  });

  it('takes a file from .open() as a chip with its name, and × drops it', async () => {
    await openChat();
    const input = screen.getByTestId('chat-file-input');
    screen.getByRole('button', { name: 'Open a data file' }).focus();
    fireEvent.change(input, {
      target: { files: [new File([TABLE], 'scores.csv', { type: 'text/csv' })] },
    });
    expect(
      await screen.findByRole('group', { name: /^Attached file scores\.csv/ })
    ).toHaveTextContent('▤ scores.csv · 4 lines');
    // The box has the focus, so Enter sends the file instead of opening the chooser again.
    expect(message()).toHaveFocus();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_file', {
      kind: 'text',
      encoding: 'utf-8',
      outcome: 'attached',
    });
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_file', {
      kind: 'text',
      encoding: 'utf-8',
      outcome: 'removed',
    });
  });

  it('reads a workbook on the server with the loader, and drops an answer that came after ×', async () => {
    let release!: () => void;
    routeDataset(path =>
      path.endsWith('/dataset/convert')
        ? (new Promise<Response>(resolve => {
            release = () =>
              resolve(
                json(200, {
                  text: 'month,revenue\nJan,120\nFeb,130\n',
                  format: 'csv',
                  kind: 'xlsx',
                  rows: 2,
                  columns: 2,
                  sheet: '2024',
                  sheets: ['2024', '2025'],
                  sheet_count: 2,
                  warnings: {},
                  dropped: [],
                })
              );
          }) as unknown as Response)
        : undefined
    );
    await openChat();
    const workbook = new File(
      [new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0, 0, 0, 0])],
      'Bericht.xlsx'
    );
    fireEvent.drop(screen.getByRole('region', { name: 'Chat' }), {
      dataTransfer: { files: [workbook], types: ['Files'] },
    });
    expect(await screen.findByTestId('attachment')).toHaveTextContent(
      'reading "Bericht.xlsx" on the server'
    );
    expect(within(chip()).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(screen.getByTestId('send-return')).toHaveAttribute('aria-disabled', 'true');
    release();
    expect(
      await screen.findByRole('group', { name: /^Attached file Bericht\.xlsx · sheet ‹2024›/ })
    ).toHaveTextContent('▤ Bericht.xlsx · sheet ‹2024› · 3 lines');

    // A second workbook, removed while the server reads it: its late answer brings nothing back.
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    fireEvent.drop(screen.getByRole('region', { name: 'Chat' }), {
      dataTransfer: { files: [workbook], types: ['Files'] },
    });
    await screen.findByText('reading "Bericht.xlsx" on the server');
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    release();
    // Long enough for the answer to be read and dropped: it never brings the chip back.
    await new Promise(resolve => setTimeout(resolve, 50));
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
  });

  it('refuses a file while a step runs, and says so under the composer', async () => {
    await openChat();
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Make example data' }));
    await waitFor(() => expect(releaseTurn).not.toBeNull());
    expect(screen.getByRole('button', { name: 'Open a data file' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
    fireEvent.drop(screen.getByRole('region', { name: 'Chat' }), {
      dataTransfer: { files: [new File([TABLE], 'b.csv', { type: 'text/csv' })], types: ['Files'] },
    });
    expect(await screen.findByTestId('attachment-notice')).toHaveTextContent(
      'a step is still running'
    );
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    releaseTurn?.();
    await turnEnded();
  });

  it('marks a table over the caps red and holds Enter and the ↵ back', async () => {
    await openChat();
    pasteText(`x,y\n${'1,2\n'.repeat(20_100)}`);
    expect(chip()).toHaveAttribute('data-status', 'over_cap');
    expect(screen.getByTestId('attachment-error')).toHaveTextContent(
      'at most 20,000 rows and 1 MB: filter first, or .open() an Excel or Parquet file (5 MB)'
    );
    expect(screen.getByTestId('send-return')).toHaveAttribute('aria-disabled', 'true');
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(datasetPosts()).toHaveLength(0);
    // Pretty-printed JSON is exempt from the line cap.
    pasteText(`[\n${'  {\n    "x": 1\n  },\n'.repeat(6000)}  {"x": 2}\n]`);
    expect(chip()).toHaveAttribute('data-status', 'ready');
  });

  it('routes a paste the browser inserted itself, and never typed lines', async () => {
    await openChat();
    // Typed on two lines (Shift+Enter): the box keeps it, a message.
    fireEvent.input(message(), {
      target: { value: 'hours,score\n1.5,52' },
      inputType: 'insertLineBreak',
    });
    expect(message()).toHaveValue('hours,score\n1.5,52');
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    // An input method's composition and a typed character keep a table-shaped box a message too.
    fireEvent.input(message(), { target: { value: TABLE }, inputType: 'insertCompositionText' });
    fireEvent.input(message(), { target: { value: `${TABLE}x` }, inputType: 'insertText' });
    expect(message()).toHaveValue(`${TABLE}x`);
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    fireEvent.input(message(), { target: { value: '' }, inputType: 'deleteContentBackward' });

    // A paste whose event hid the text (iOS Safari): the inserted table becomes the chip.
    fireEvent.input(message(), { target: { value: TABLE }, inputType: 'insertFromPaste' });
    expect(chip()).toHaveAccessibleName(/^Attached table, 4 lines/);
    expect(message()).toHaveValue('');
  });

  it('counts a message paste once, though the browser reports its insertion again', async () => {
    await openChat();
    const routed = () =>
      analytics.trackEvent.mock.calls.filter(([name]) => name === 'agent_input_routed');
    // The paste event routes the text as a message; the browser then inserts it and fires the
    // input event jsdom leaves out, with `insertFromPaste` too.
    expect(pasteText('a bar chart, please')).toBe(true);
    fireEvent.input(message(), {
      target: { value: 'a bar chart, please' },
      inputType: 'insertFromPaste',
    });
    expect(message()).toHaveValue('a bar chart, please');
    expect(routed()).toEqual([['agent_input_routed', { as: 'message', via: 'paste' }]]);

    // The next paste the event hid (iOS) is routed on its input: the first one's mark is spent.
    fireEvent.input(message(), { target: { value: '' }, inputType: 'deleteContentBackward' });
    fireEvent.input(message(), { target: { value: TABLE }, inputType: 'insertFromPaste' });
    expect(chip()).toHaveAccessibleName(/^Attached table, 4 lines/);
    expect(routed()).toHaveLength(2);

    // A table the paste event took inserts nothing, so it leaves no mark for the next paste.
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    expect(pasteText(TABLE)).toBe(false);
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    fireEvent.input(message(), { target: { value: TABLE }, inputType: 'insertFromPaste' });
    expect(chip()).toHaveAccessibleName(/^Attached table, 4 lines/);
    expect(routed()).toHaveLength(4);
  });

  it('lets the plot button take a chip along, and asks before a reload drops it', async () => {
    await openChat();
    const unload = () => {
      const event = new Event('beforeunload', { cancelable: true });
      window.dispatchEvent(event);
      return event.defaultPrevented;
    };
    expect(unload()).toBe(false);
    fireEvent.change(message(), { target: { value: 'a draft' } });
    expect(unload()).toBe(true);
    fireEvent.change(message(), { target: { value: '' } });
    expect(unload()).toBe(false);

    await parseAndSummarize();
    pasteText(TABLE);
    expect(unload()).toBe(true);
    const create = screen.getByRole('button', { name: 'Create plot' });
    expect(create).not.toHaveAttribute('aria-disabled');
    // The session holds data: the line says that the table replaces it, for good.
    expect(create).toHaveAccessibleDescription(
      'step 1 of 2 · the attached table replaces your data (2 rows, no .undo()) · .create_plot() reads and plots it, Enter ↵ only reads it'
    );
  });

  it('keeps the plot button inert while a chip is too large to send, as Enter is', async () => {
    await openChat();
    pasteText(`x,y\n${'1,2\n'.repeat(20_100)}`);
    expect(chip()).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'step 1 of 2 · the attached table is read when you press Enter ↵, with a note if you like'
    );
  });

  describe('one click on the plot button', () => {
    /** A summary that asks nothing: the reading is clean. */
    const CLEAN = 'Read 3 rows: hours on x, score on y.';
    /** Answers the turns `answer` names before the rest of the stub, held back as the stub holds one. */
    function routeTurns(
      answer: (body: { text?: string; action?: string }) => [string, unknown][] | undefined
    ) {
      const base = fetchMock.getMockImplementation() as (
        input: string,
        init?: RequestInit
      ) => Promise<Response>;
      fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
        if (pathOf(input).endsWith('/sessions/S1/messages') && init.method === 'POST') {
          const events = answer(JSON.parse(String(init.body)));
          if (events) {
            const response = sse(events);
            if (!holdNextTurn) return response;
            holdNextTurn = false;
            return new Promise<Response>(resolve => {
              releaseTurn = () => resolve(response);
            });
          }
        }
        return base(input, init);
      });
    }
    const cleanSummary = () =>
      routeTurns(body =>
        body.action === 'summarize_data'
          ? [
              ['message', { text: CLEAN }],
              ['done', { llm_calls: 1 }],
            ]
          : undefined
      );
    const bindingPuts = () =>
      agentCalls().filter(
        ([input, init]) =>
          pathOf(input).endsWith('/bindings') && (init as RequestInit | undefined)?.method === 'PUT'
      );
    const step = () => screen.getByTestId('data-step');
    const clickCreate = async () => {
      const create = screen.getByRole('button', { name: 'Create plot' });
      await untilActive(create);
      fireEvent.click(create);
    };

    it('reads the chip with its note, then confirms and plots, once', async () => {
      routeTurns(body =>
        body.text === 'make the bars blue'
          ? [
              ['message', { text: `${CLEAN} The blue bars are kept for the first plot.` }],
              ['done', { llm_calls: 1, turn: 'kept' }],
            ]
          : undefined
      );
      await openChat();
      pasteText(TABLE);
      fireEvent.change(message(), { target: { value: 'make the bars blue' } });
      await clickCreate();
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      await turnEnded();
      // The note went with the table as its first turn; the page went on by itself, once.
      expect(confirmAndTurns()).toEqual(['text: make the bars blue', 'confirm', 'create_plot']);
      expect(datasetPosts()).toHaveLength(1);
      expect(message()).toHaveValue('');
      expect(lastAction()).toHaveTextContent(/^❯\.create_plot\(\)# matplotlib$/);
      expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    });

    it.each([
      ['a short CSV', TABLE],
      [
        'a 5 KB CSV',
        [
          'hours,score',
          ...Array.from({ length: 400 }, (_, i) => `${i + 1}.5,${50 + (i % 40)}`),
        ].join('\n'),
      ],
      [
        'cells copied from a spreadsheet',
        ['hours\tscore', '1.5\t52', '2.0\t58', '3.0\t61'].join('\r\n'),
      ],
    ])('makes %s, the first paste of a fresh session, one click from its plot', async (_, text) => {
      cleanSummary();
      await openChat();
      // The paste is the page's first action: no turn ran, nothing is stored.
      const create = screen.getByRole('button', { name: 'Create plot' });
      expect(create).toHaveAttribute('aria-disabled', 'true');
      expect(confirmAndTurns()).toEqual([]);
      pasteText(text);
      expect(chip()).toBeInTheDocument();
      expect(message()).toHaveValue('');
      // Active at once, as Enter would send it now: a long paste counts by the dataset's limits.
      expect(create).not.toHaveAttribute('aria-disabled');
      expect(step()).toHaveTextContent(
        'step 1 of 2 · .create_plot() reads the attached table and plots it · Enter ↵ only reads it'
      );
      fireEvent.click(create);
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      await turnEnded();
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
      expect(datasetPosts()).toHaveLength(1);
      expect(JSON.parse(String((datasetPosts()[0][1] as RequestInit).body)).text).toBe(text);
    });

    it('reads a pasted table with all pressed, then plots it in every library', async () => {
      cleanSummary();
      await openChat();
      await toggleAll();
      const plotAll = screen.getByRole('button', { name: 'Plot in all libraries' });
      expect(plotAll).toHaveAttribute('aria-disabled', 'true');
      pasteText(TABLE);
      // Enter would read it: the button reads it too, and plots it where `all` says.
      expect(plotAll).not.toHaveAttribute('aria-disabled');
      expect(step()).toHaveTextContent(
        'step 1 of 2 · .plot_all() reads the attached table and plots it · Enter ↵ only reads it'
      );
      fireEvent.click(plotAll, { detail: 1 });
      const panel = await screen.findByRole('region', { name: 'All libraries' });
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm']);
      expect(datasetPosts()).toHaveLength(1);
      expect(
        within(panel)
          .getAllByRole('article')
          .map(card => card.getAttribute('aria-label'))
      ).toEqual(['matplotlib', 'seaborn']);
      // A pointer click moves no focus.
      expect(panel).not.toHaveFocus();
    });

    it('takes the focus into the fan-out it opened after reading, when a key pressed it', async () => {
      cleanSummary();
      await openChat();
      await toggleAll();
      pasteText(TABLE);
      // A key press is a click with `detail` 0: the panel the chain opens takes the focus.
      fireEvent.click(screen.getByRole('button', { name: 'Plot in all libraries' }), { detail: 0 });
      expect(await screen.findByRole('region', { name: 'All libraries' })).toHaveFocus();
    });

    it('says that it reads while the reading runs, and plots after it', async () => {
      cleanSummary();
      await openChat();
      pasteText(TABLE);
      holdNextTurn = true;
      await clickCreate();
      await waitFor(() => expect(releaseTurn).not.toBeNull());
      expect(step()).toHaveTextContent(
        'step 1 of 2 · reading your data · the plot follows by itself unless something needs a look'
      );
      expect(screen.getByRole('button', { name: 'Create plot' })).toHaveAttribute(
        'aria-disabled',
        'true'
      );
      act(() => releaseTurn?.());
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
    });

    it('reads a table typed into the box and plots it in the same click', async () => {
      cleanSummary();
      await openChat();
      fireEvent.change(message(), { target: { value: TABLE } });
      await clickCreate();
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
      expect(String((datasetPosts()[0][1] as RequestInit).body)).toContain('hours,score');
    });

    it('stops at the card on a warning of the data, and the next click plots', async () => {
      cleanSummary();
      routeDataset((path, init) =>
        path.endsWith('/dataset') && init.method === 'POST'
          ? json(200, { ...pasted(), warnings: ["score: 1 cell read as missing ('n/a')"] })
          : undefined
      );
      await openChat();
      pasteText(TABLE);
      await clickCreate();
      expect(await screen.findByText(CLEAN)).toBeInTheDocument();
      await turnEnded();
      await waitFor(() =>
        expect(step()).toHaveTextContent(
          'step 1 of 2 · 1 warning on the data · check above, then .create_plot()'
        )
      );
      expect(confirmAndTurns()).toEqual(['summarize_data']);
      await clickCreate();
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
    });

    it("stops at the card on the assistant's question", async () => {
      await openChat();
      pasteText(TABLE);
      await clickCreate();
      expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
      await turnEnded();
      await waitFor(() =>
        expect(step()).toHaveTextContent(
          'step 1 of 2 · the assistant asked a question · answer it in the box, or .create_plot()'
        )
      );
      expect(confirmAndTurns()).toEqual(['summarize_data']);
      // A message is a change: the stop's words go, the step's own line is back.
      sendFromComposer('what is the mean');
      expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
      await turnEnded();
      expect(step()).toHaveTextContent(
        'step 1 of 2 · check the data and the bindings above, then .create_plot()'
      );
    });

    it("stops at the card on a warning of the server's binding check", async () => {
      cleanSummary();
      const base = fetchMock.getMockImplementation() as (
        input: string,
        init?: RequestInit
      ) => Promise<Response>;
      fetchMock.mockImplementation(async (input: string, init: RequestInit = {}) => {
        if (pathOf(input).endsWith('/bindings') && init.method === 'PUT') {
          return json(200, {
            bindings: JSON.parse(String(init.body)),
            complete: true,
            missing_roles: [],
            warnings: [
              "x: column 'hours' holds 2 values in 3 rows; the plot draws one value per x, so rows with the same x need an aggregate first",
            ],
          });
        }
        return base(input, init);
      });
      await openChat();
      pasteText(TABLE);
      await clickCreate();
      expect(await screen.findByText(CLEAN)).toBeInTheDocument();
      await turnEnded();
      await waitFor(() =>
        expect(step()).toHaveTextContent(
          'step 1 of 2 · a warning on x · check it above, then .create_plot()'
        )
      );
      expect(confirmAndTurns()).toEqual(['summarize_data']);
      // The card shows the line the stop points at: no bound column's own warning holds it.
      expect(screen.getByTestId('binding-warning')).toHaveTextContent(
        "x: column 'hours' holds 2 values in 3 rows"
      );
    });

    it('plots nothing when the user opened .change() on the card while the reading ran', async () => {
      cleanSummary();
      await openChat();
      pasteText(TABLE);
      holdNextTurn = true;
      await clickCreate();
      await waitFor(() => expect(releaseTurn).not.toBeNull());
      fireEvent.click(await screen.findByRole('button', { name: 'Change the bindings' }));
      expect(step()).not.toHaveTextContent('reading your data');
      act(() => releaseTurn?.());
      expect(await screen.findByText(CLEAN)).toBeInTheDocument();
      await turnEnded();
      expect(confirmAndTurns()).toEqual(['summarize_data']);
    });

    it('asks the binding check again after the reading changed the data, then plots', async () => {
      routeTurns(body =>
        body.text === 'score in prozent'
          ? [
              ['message', { text: 'I read score as numbers.' }],
              [
                'done',
                {
                  llm_calls: 2,
                  bindings: PREPARED.bindings,
                  data_confirmed: false,
                  dataset: changedVersion(PREPARED),
                },
              ],
            ]
          : undefined
      );
      await openChat();
      pasteText(TABLE);
      fireEvent.change(message(), { target: { value: 'score in prozent' } });
      await clickCreate();
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      // The parse's own check, then one for the version the turn made.
      expect(bindingPuts()).toHaveLength(2);
      expect(confirmAndTurns()).toEqual(['text: score in prozent', 'confirm', 'create_plot']);
    });

    it('stops at the card when the reading ends in a refusal or an error', async () => {
      routeTurns(body =>
        body.text === 'write me a poem'
          ? [
              ['refusal', { code: 'out_of_scope', text: 'I only work on this plot.' }],
              ['done', { llm_calls: 1 }],
            ]
          : body.text === 'break it'
            ? [
                ['error', { code: 'internal', ref: 'r-1' }],
                ['done', { llm_calls: 1 }],
              ]
            : body.action === 'summarize_data'
              ? [
                  ['message', { text: CLEAN }],
                  ['done', { llm_calls: 1 }],
                ]
              : undefined
      );
      await openChat();
      pasteText(TABLE);
      fireEvent.change(message(), { target: { value: 'write me a poem' } });
      await clickCreate();
      // The refused note's data still gets its summary, and the chain stops after it.
      expect(await screen.findByText(CLEAN)).toBeInTheDocument();
      await turnEnded();
      await waitFor(() =>
        expect(step()).toHaveTextContent(
          'step 1 of 2 · the reading ended in a refusal · see above, then .create_plot()'
        )
      );
      expect(confirmAndTurns()).toEqual(['text: write me a poem', 'summarize_data']);

      pasteText(TABLE);
      fireEvent.change(message(), { target: { value: 'break it' } });
      await clickCreate();
      await waitFor(() =>
        expect(step()).toHaveTextContent(
          'step 1 of 2 · the reading ended in an error · see above, then .create_plot()'
        )
      );
      expect(confirmAndTurns()).not.toContain('confirm');
    });

    it('plots nothing when the user typed while the reading ran', async () => {
      cleanSummary();
      await openChat();
      pasteText(TABLE);
      holdNextTurn = true;
      await clickCreate();
      await waitFor(() => expect(releaseTurn).not.toBeNull());
      fireEvent.change(message(), { target: { value: 'log scale' } });
      expect(step()).not.toHaveTextContent('reading your data');
      act(() => releaseTurn?.());
      await turnEnded();
      expect(confirmAndTurns()).toEqual(['summarize_data']);
      expect(message()).toHaveValue('log scale');
      // The next click is the user's, with the text as the plot's request.
      await clickCreate();
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'text: log scale']);
    });

    it('names new data after a plot, and plots the new data in one click', async () => {
      await openChat();
      await parseAndPlot();
      cleanSummary();
      pasteText(TABLE);
      const button = screen.getByRole('button', { name: 'Plot the new data' });
      expect(button).not.toHaveAttribute('aria-disabled');
      fireEvent.click(button);
      await waitFor(() =>
        expect(lastAction()).toHaveTextContent(/^❯plot the new data# matplotlib$/)
      );
      await turnEnded();
      // The new data's plot is "plot the new data" (`plot_new_data`), which the server starts from
      // the catalogue plot here, since the paste is other data.
      expect(confirmAndTurns()).toEqual([
        'summarize_data',
        'confirm',
        'create_plot',
        'summarize_data',
        'confirm',
        'plot_new_data',
      ]);
    });

    it('ends at a table read from text, which stores nothing, with its decision on the line', async () => {
      await openChat();
      pasteText(FREE_TEXT);
      await clickCreate();
      await screen.findByTestId('transcription-card');
      await waitFor(() =>
        expect(step()).toHaveTextContent(
          'step 1 of 2 · decide on the table first: .use() or .discard()'
        )
      );
      expect(confirmAndTurns()).toEqual([]);
    });

    it('leaves Enter as it was: it reads the chip and plots nothing', async () => {
      cleanSummary();
      await openChat();
      pasteText(TABLE);
      fireEvent.keyDown(message(), { key: 'Enter' });
      expect(await screen.findByText(CLEAN)).toBeInTheDocument();
      await turnEnded();
      expect(confirmAndTurns()).toEqual(['summarize_data']);
      expect(step()).toHaveTextContent(
        'step 1 of 2 · check the data and the bindings above, then .create_plot()'
      );
    });
  });

  it('keeps the attached table out of the browser storage', async () => {
    const writes = vi.spyOn(Storage.prototype, 'setItem');
    await openChat();
    pasteText(TABLE);
    fireEvent.change(message(), { target: { value: 'secret note' } });
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByText('Swapped.');
    await turnEnded();
    const written = writes.mock.calls.map(([, value]) => String(value)).join('\n');
    expect(written).not.toContain('hours,score');
    expect(written).not.toContain('secret note');
    writes.mockRestore();
  });

  const csvFile = (text: string, name: string) => new File([text], name, { type: 'text/csv' });
  const workbook = (name = 'Bericht.xlsx') =>
    new File([new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0, 0, 0, 0])], name);
  const dropOnChat = (...files: File[]) =>
    fireEvent.drop(screen.getByRole('region', { name: 'Chat' }), {
      dataTransfer: { files, types: ['Files'] },
    });
  const converted = (overrides: Record<string, unknown> = {}) =>
    json(200, {
      text: 'month,revenue\nJan,120\nFeb,130\n',
      format: 'csv',
      kind: 'xlsx',
      rows: 2,
      columns: 2,
      sheet: '2024',
      sheets: ['2024', '2025'],
      sheet_count: 2,
      warnings: {},
      dropped: [],
      ...overrides,
    });

  it('reads the first of several files, CRLF breaks as the box holds them, and names it on the chip', async () => {
    await openChat();
    dropOnChat(csvFile('a,b\r\n1,2\r\n3,4\r\n', 'windows.csv'), csvFile('c\n', 'c.csv'));
    expect(
      await screen.findByRole('group', { name: 'Attached file windows.csv, 3 lines, 12 B' })
    ).toBeInTheDocument();
    expect(screen.getByText('# first of 2 files read — one file at a time')).toBeInTheDocument();
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByText(SUMMARY);
    await turnEnded();
    // The text goes with its line breaks as the parser reads them, and the file's name as `source`.
    expect(JSON.parse(String((datasetPosts()[0][1] as RequestInit).body))).toMatchObject({
      text: 'a,b\n1,2\n3,4\n',
      source: 'windows.csv',
    });
  });

  it('names what the server counted in a workbook, and keeps the file for the sheet picker', async () => {
    routeDataset(path =>
      path.endsWith('/dataset/convert')
        ? converted({
            warnings: { formulas_without_value: 3, dropped_columns: 3 },
            dropped: ['span', 'raw'],
          })
        : undefined
    );
    await openChat();
    dropOnChat(workbook());
    const attached = await screen.findByRole('group', { name: /^Attached file Bericht\.xlsx/ });
    expect(attached.parentElement).toHaveTextContent(
      'on the server: sheet ‹2024› of xlsx · 2 rows × 2 columns'
    );
    expect(attached.parentElement).toHaveTextContent('3 formula cells saved without a value');
    expect(attached.parentElement).toHaveTextContent(
      '3 columns of durations, intervals, binary, map or nested values left out: "span", "raw" and 1 more'
    );
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByText(SUMMARY);
    await turnEnded();
    expect(screen.getByLabelText(/# sheet/)).toHaveValue('2024');
  });

  it('holds the composer back while another sheet is read, then parses that sheet', async () => {
    let finish: (() => void) | null = null;
    routeDataset(path => {
      if (!path.endsWith('/dataset/convert')) return undefined;
      // The first read attaches the workbook; the sheet picker's read waits for `finish`.
      if (!finish) {
        finish = () => {};
        return converted();
      }
      return new Promise<Response>(resolve => {
        finish = () =>
          resolve(converted({ sheet: '2025', text: 'month,revenue\nJan,90\nFeb,95\n' }));
      }) as unknown as Response;
    });
    await openChat();
    dropOnChat(workbook());
    await screen.findByRole('group', { name: /^Attached file Bericht\.xlsx/ });
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByText(SUMMARY);
    await turnEnded();
    const posts = datasetPosts().length;
    const turns = turnBodies().length;

    fireEvent.change(screen.getByLabelText(/# sheet/), { target: { value: '2025' } });
    await screen.findByTestId('sheet-reading');
    // Nothing plots, confirms or sends while the read runs: the parse after it would be skipped.
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
    fireEvent.change(message(), { target: { value: 'which month sold most?' } });
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(turnBodies()).toHaveLength(turns);

    finish!();
    await waitFor(() => expect(datasetPosts()).toHaveLength(posts + 1));
    expect(JSON.parse(String((datasetPosts()[posts][1] as RequestInit).body))).toMatchObject({
      text: 'month,revenue\nJan,90\nFeb,95\n',
      source: 'Bericht.xlsx · sheet ‹2025›',
    });
  });

  it('says why a file was not taken: a refused conversion, a pickle, a second file while one is read', async () => {
    let finish!: () => void;
    let converts = 0;
    routeDataset(path => {
      if (!path.endsWith('/dataset/convert')) return undefined;
      converts += 1;
      if (converts === 1) {
        return json(422, {
          detail: 'file_too_many_rows',
          ref: 'ref-1',
          measured: 21000,
          limit: 20000,
        });
      }
      return new Promise<Response>(resolve => {
        finish = () => resolve(converted());
      }) as unknown as Response;
    });
    await openChat();

    dropOnChat(workbook('big.xlsx'));
    expect(await screen.findByTestId('attachment-notice')).toHaveTextContent(
      '"big.xlsx" has more rows than a table may have; filter it, or copy a range and paste it (21,000 rows, the cap is 20,000)'
    );
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();

    dropOnChat(new File([new Uint8Array([0x80, 0x05, 0x95])], 'frame.pkl'));
    expect(await screen.findByTestId('attachment-notice')).toHaveTextContent(
      'never read because loading one can run code'
    );
    expect(converts).toBe(1);

    dropOnChat(workbook());
    await screen.findByText('reading "Bericht.xlsx" on the server');
    expect(screen.getByRole('button', { name: 'Open a data file' })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
    dropOnChat(csvFile(TABLE, 'b.csv'));
    expect(await screen.findByTestId('attachment-notice')).toHaveTextContent(
      'a file is still being read on the server'
    );
    finish();
    expect(
      await screen.findByRole('group', { name: /^Attached file Bericht\.xlsx/ })
    ).toBeInTheDocument();
  });

  it('keeps a table pasted after × of a file still read on the server, when the read lands', async () => {
    let finish!: () => void;
    routeDataset(path => {
      if (!path.endsWith('/dataset/convert')) return undefined;
      return new Promise<Response>(resolve => {
        finish = () => resolve(converted());
      }) as unknown as Response;
    });
    await openChat();
    dropOnChat(workbook());
    await screen.findByText('reading "Bericht.xlsx" on the server');
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));
    pasteText(TABLE);
    await screen.findByRole('group', { name: /^Attached table, 4 lines/ });
    finish();
    await new Promise(resolve => setTimeout(resolve, 20));
    expect(chip()).toHaveAccessibleName(/^Attached table, 4 lines/);
  });

  it('reads a file pasted from the file manager, and lets text beside a picture paste as text', async () => {
    await openChat();
    fireEvent.paste(message(), {
      clipboardData: { files: [csvFile(TABLE, 'pasted.tsv')], getData: () => '' },
    });
    expect(
      await screen.findByRole('group', { name: /^Attached file pasted\.tsv/ })
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));

    // Excel puts a picture of the cells next to their text: the text wins, and one line is typed text.
    const picture = new File([new Uint8Array([0x89, 0x50])], 'cells.png', { type: 'image/png' });
    expect(
      fireEvent.paste(message(), {
        clipboardData: { files: [picture], getData: () => '2026-03,150' },
      })
    ).toBe(true);
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
  });

  it('drops the result of a slow read that a later file superseded, and keeps stray drops on the page', async () => {
    await openChat();
    let release: (buffer: ArrayBuffer) => void = () => {};
    const slow = csvFile('slow,file\n1,2\n', 'slow.csv');
    const slowBytes = await slow.arrayBuffer();
    slow.arrayBuffer = () =>
      new Promise<ArrayBuffer>(resolve => {
        release = resolve;
      });
    dropOnChat(slow);
    dropOnChat(csvFile(TABLE, 'fast.csv'));
    await screen.findByRole('group', { name: /^Attached file fast\.csv/ });
    release(slowBytes);
    await new Promise(resolve => setTimeout(resolve, 20));
    expect(screen.getByRole('group', { name: /^Attached file fast\.csv/ })).toBeInTheDocument();

    // A file dropped beside the chat: prevented, so the page stays; a text drag keeps its default.
    const transfer = { files: [], types: ['Files'], dropEffect: 'none' };
    expect(fireEvent.drop(document.body, { dataTransfer: transfer })).toBe(false);
    expect(fireEvent.drop(document.body, { dataTransfer: { types: ['text/plain'] } })).toBe(true);
    // Over the chat, the composer says whether a drop attaches.
    fireEvent.dragEnter(screen.getByRole('region', { name: 'Chat' }), { dataTransfer: transfer });
    expect(screen.getByTestId('drop-hint')).toHaveTextContent('drop the file to attach it');
    fireEvent.dragLeave(screen.getByRole('region', { name: 'Chat' }), { dataTransfer: transfer });
    expect(screen.queryByTestId('drop-hint')).not.toBeInTheDocument();
  });

  it('sends a formula file to the chat as the user turn, and asks to shorten code it cannot take', async () => {
    let refuseCode = false;
    routeDataset((path, init) => {
      if (!path.endsWith('/dataset') || init.method !== 'POST' || !refuseCode) return undefined;
      return json(422, { detail: 'code', ref: 'r-c' });
    });
    await openChat();
    fireEvent.change(screen.getByTestId('chat-file-input'), {
      target: { files: [csvFile(FORMULA, 'curve.txt')] },
    });
    await screen.findByRole('group', { name: /^Attached file curve\.txt/ });
    fireEvent.change(message(), { target: { value: 'a note' } });
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(await screen.findByText('I generated 200 rows from y = sin(x).')).toBeInTheDocument();
    await turnEnded();
    expect(turnBodies()).toEqual([{ text: FORMULA }]);
    expect(screen.queryByTestId('attachment')).not.toBeInTheDocument();
    // The note did not go with a forward: it is back in the box.
    expect(message()).toHaveValue('a note');

    refuseCode = true;
    fireEvent.change(message(), { target: { value: '' } });
    fireEvent.change(screen.getByTestId('chat-file-input'), {
      target: { files: [csvFile('x = np.arange(10)\n'.repeat(200), 'long.py')] },
    });
    await screen.findByRole('group', { name: /^Attached file long\.py/ });
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(await screen.findByTestId('attachment-error')).toHaveTextContent(
      'looks like code that makes data: shorten it to 2,000 characters, keeping only the part that computes the data, and the chat runs it'
    );
  });

  it('opens the new data card after a file sent over a table read from text in step 2', async () => {
    await openChat();
    await parseAndPlot();
    await attachAndSend(FREE_TEXT);
    expect(await screen.findByTestId('transcription-card')).toBeInTheDocument();
    dropOnChat(csvFile('hours,score\n3,70\n4,80\n', 'new.csv'));
    await screen.findByRole('group', { name: /^Attached file new\.csv/ });
    fireEvent.keyDown(message(), { key: 'Enter' });
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    // New data nobody confirmed: step 1, its card open, the table read from text gone.
    expect(currentStep()).toBe(1);
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(screen.queryByTestId('transcription-card')).not.toBeInTheDocument();
    expect(JSON.parse(String((datasetPosts().slice(-1)[0][1] as RequestInit).body))).toMatchObject({
      source: 'new.csv',
    });
  });

  it('puts the text back into the box on .discard() of the table read from it', async () => {
    await openChat();
    await attachAndSend(FREE_TEXT);
    await screen.findByTestId('transcription-card');
    fireEvent.change(message(), { target: { value: 'typed meanwhile' } });
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(screen.queryByTestId('transcription-card')).not.toBeInTheDocument();
    expect(message()).toHaveValue(`${FREE_TEXT}\n\ntyped meanwhile`);
  });

  it('gives a file, or text the box could not send, back as the attachment on .discard()', async () => {
    await openChat();
    fireEvent.change(screen.getByTestId('chat-file-input'), {
      target: { files: [csvFile(FREE_TEXT, 'tiere.txt')] },
    });
    await screen.findByRole('group', { name: /^Attached file tiere\.txt/ });
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByTestId('transcription-card');
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    // The file's text waits as the file again, its name with it, and the box stays empty.
    expect(chip()).toHaveAccessibleName(/^Attached file tiere\.txt, 3 lines/);
    expect(message()).toHaveValue('');
    fireEvent.click(screen.getByRole('button', { name: 'Remove the attachment' }));

    // Over 2,000 characters a paste is no message: it comes back as the attachment too.
    const long = `${FREE_TEXT}\n${'Pferd 1, Esel 5\n'.repeat(140)}`;
    pasteText(long);
    await screen.findByRole('group', { name: /^Attached table/ });
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByTestId('transcription-card');
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(chip()).toHaveAccessibleName(/^Attached table, 143 lines/);
    expect(message()).toHaveValue('');

    // An attachment made while the table waited stays: the discarded one does not replace it.
    fireEvent.keyDown(message(), { key: 'Enter' });
    await screen.findByTestId('transcription-card');
    pasteText(TABLE);
    await screen.findByRole('group', { name: /^Attached table, 4 lines/ });
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(chip()).toHaveAccessibleName(/^Attached table, 4 lines/);
  });

  it('sends on Enter and Ctrl+Enter, never inside a composition or on Shift+Enter, and never cuts a long text', async () => {
    await openChat();
    fireEvent.change(message(), { target: { value: 'what is the mean score?' } });
    fireEvent.keyDown(message(), { key: 'Enter', shiftKey: true });
    fireEvent.keyDown(message(), { key: 'Enter', isComposing: true });
    expect(turnBodies()).toEqual([]);
    fireEvent.keyDown(message(), { key: 'Enter', ctrlKey: true });
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();

    // Over the cap: the whole text stays, the counter turns red, Enter and the `↵` wait.
    const long = 'a'.repeat(2001);
    fireEvent.change(message(), { target: { value: long } });
    expect(message()).toHaveValue(long);
    expect(message()).not.toHaveAttribute('maxlength');
    expect(message()).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByTestId('message-counter')).toHaveTextContent('2,001 / 2,000');
    expect(screen.getByTestId('composer-status')).toHaveTextContent(
      'the message is longer than 2,000 characters'
    );
    expect(screen.getByTestId('send-return')).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(screen.getByTestId('send-return'));
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(turnBodies()).toHaveLength(1);
  });

  it("keeps the how-to of the data behind the ⓘ at the end of the start item's pointer to the box", async () => {
    await openChat();
    // The header row had it until the start item took it: the ⓘ ends the item's last line,
    // "drop a file or paste a table below", in the thread.
    const howto = screen.getByRole('button', { name: 'How the chat takes data' });
    expect(screen.queryByText('# chat')).not.toBeInTheDocument();
    const start = screen.getByTestId('start-item');
    expect(screen.getByRole('log', { name: 'Conversation' })).toContainElement(start);
    const hint = screen.getByTestId('start-hint');
    expect(hint).toHaveTextContent(/^drop a file or paste a table below$/);
    expect(hint).toContainElement(howto);
    expect(start).toContainElement(hint);
    fireEvent.click(howto);
    const dialog = await screen.findByRole('dialog', { name: 'How the chat takes data' });
    expect(within(dialog).getByTestId('data-howto').children).toHaveLength(7);
    expect(dialog).toHaveTextContent(
      'paste or drop a table or a file: it waits in the message box until Enter'
    );
    expect(dialog).toHaveTextContent(
      'type a note with it: "only 2024", "the decimal mark is a comma"'
    );
  });
});
