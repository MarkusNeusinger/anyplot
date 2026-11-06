import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import type { MemoryEntry } from 'src/lib/agent';
import { AgentChatPage } from 'src/pages/AgentChatPage';
import { LEAVE_TEXT, servicePausedText } from 'src/sections/agent-chat/messages';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

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
  // The first plot: `.create_plot()` as it is, or with a change the user typed first.
  if (body.action === 'create_plot' || body.text?.includes('log scale')) {
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
          dataset: { ...GENERATED, changes: ['generated example data: 200 rows, 2 columns'] },
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
        { llm_calls: 2, bindings: GENERATED.bindings, data_confirmed: false, dataset: GENERATED },
      ],
    ];
  }
  // The assistant's `prepare_data` changed the data; `done` carries the new version.
  if (body.text?.includes('prozent')) {
    return [
      ['message', { text: 'I read score as numbers.' }],
      [
        'done',
        { llm_calls: 2, bindings: PREPARED.bindings, data_confirmed: false, dataset: PREPARED },
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
      return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true });
    }
    if (url.pathname.endsWith('/sessions/S1/dataset') && method === 'POST') {
      const text = String(init.body);
      // A formula is refused: the chat computes it.
      if (text.includes('sin(')) return json(422, { detail: 'formula', ref: 'r-f' });
      if (text.includes('Hund')) return json(200, TRANSCRIBED);
      if (text.includes('slow')) {
        return new Promise<Response>(resolve => {
          releaseParse = () => resolve(json(200, DATASET));
        });
      }
      return json(200, DATASET);
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
      return json(200, DATASET);
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
        path: '/debug/agent',
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

const PAGE = '/debug/agent?spec=scatter-basic&library=matplotlib&language=python';
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
  await waitFor(() => expect(create).toBeEnabled());
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

/** The composer's step buttons, in order: `.open()`, which stands in every state, is left out. */
const composerButtons = () =>
  within(screen.getByLabelText('Message').closest('form') as HTMLElement)
    .queryAllByRole('button')
    .map(button => button.textContent)
    .filter(label => label !== '.open()');

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

/** Pick `name` in the library menu (a library, or `All libraries`), and wait until it closed. */
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
  releaseParse = null;
  holdNextTurn = false;
  releaseTurn = null;
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

  it('asks for the admin sign-in without the admin hint and calls nothing', () => {
    renderAt(PAGE);
    expect(screen.getByText(/this page is for admins/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '/debug' })).toHaveAttribute('href', '/debug');
    expect(agentCalls()).toHaveLength(0);
  });

  it('opens a session for an admin and records the open, then drops the source', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&source=plot_page`);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Attach a data file' })).toBeInTheDocument();
    expect(analytics.trackPageview).toHaveBeenCalledWith('/debug/agent');
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
      library: 'matplotlib',
      source: 'plot_page',
      spec: 'scatter-basic',
    });
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(PAGE));
    // The title in plain words is the link back, in the frame's header row (`← title` until v4).
    const back = await screen.findByRole('link', { name: 'Basic Scatter Plot' });
    expect(back).toHaveAttribute('href', expect.stringContaining('scatter-basic'));
    expect(screen.getByRole('region', { name: 'Chat' })).toContainElement(back);
    expect(screen.getByTestId('chat-frame-tab')).toHaveTextContent(/^~\/anyplot\.ai\/agent$/);
  });

  it('names the tab after the spec title, not its id', async () => {
    flags.isDev = true;
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    await waitFor(() => expect(document.title).toBe('agent · Basic Scatter Plot | anyplot.ai'));
  });

  it('lets local development in without the hint', async () => {
    flags.isDev = true;
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith(
      'agent_open',
      expect.objectContaining({ source: 'direct' })
    );
  });

  it('explains the missing parameters instead of calling the BFF', () => {
    flags.isDev = true;
    renderAt('/debug/agent?spec=scatter-basic&library=excel');
    // The plot page's entry since 2026-11-02 is `.use_my_data()`.
    expect(screen.getByText(/open it from a plot/)).toHaveTextContent(
      "open it from a plot's .use_my_data(), or start with scatter-basic in matplotlib."
    );
    expect(screen.getByRole('link', { name: 'scatter-basic in matplotlib' })).toHaveAttribute(
      'href',
      '/debug/agent?spec=scatter-basic&library=matplotlib&language=python'
    );
    expect(agentCalls()).toHaveLength(0);
  });

  it('clears the hint and asks for the sign-in when the BFF refuses the admin', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubFetch(401);
    renderAt(PAGE);
    expect(await screen.findByText(/this page is for admins/)).toBeInTheDocument();
    await waitFor(() => expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull());
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
        '/debug/agent?spec=scatter-basic&library=seaborn&language=python'
      )
    );
    expect(within(menu).getByRole('button', { name: 'matplotlib' })).toBeDisabled();
    expect(within(menu).queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
  });

  it('walks the two steps with one click: .create_plot() confirms the data, then plots', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    expect(await screen.findByLabelText('Message')).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    // Before data the status line names the step and the data; the how-to is behind the header
    // row's ⓘ, not in a paragraph on the page (2026-11-02).
    expect(screen.getByTestId('data-step')).toHaveTextContent(/^>>> step 1 of 2 · your data$/);
    expect(screen.queryByText(/check the preview and the bindings/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'How the chat takes data' })).toBeInTheDocument();

    await parseAndSummarize();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await waitFor(() => expect(create).toBeEnabled());
    // From the moment data is stored, the one action is `.create_plot()`, filled at the
    // composer's end; with an empty box there is nothing to `.send()`.
    expect(composerButtons()).toEqual(['.create_plot()']);
    expect(create).toHaveAttribute('type', 'button');
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
      'step 1 of 2 · check the preview and the bindings above, then .create_plot()'
    );
    expect(create).toHaveAccessibleDescription(
      'step 1 of 2 · check the preview and the bindings above, then .create_plot()'
    );
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the first plot should do'
    );

    holdNextTurn = true;
    fireEvent.click(create);
    // The card folds with the click and the run starts: the confirmation came first.
    await screen.findByTestId('data-pinned');
    await waitFor(() =>
      expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot'])
    );
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(currentStep()).toBe(2);
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'data fits · 2 rows · 2 columns · version 1'
    );
    // The button waits in its place beside `.stop()` while its run lasts.
    expect(composerButtons()).toEqual(['.stop()', '.create_plot()']);
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeDisabled();
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 2: the data is confirmed; create the plot below'
    );
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_confirmed', {
      size_bucket: 'lt_1kb',
    });
    // While it plots, the status line names the one action left, in the step's words' place.
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · plotting… \.stop\(\) to cancel$/
    );
    expect(screen.queryByText(/create the plot as it is/)).not.toBeInTheDocument();
    expect(lastAction()).toHaveTextContent(/^❯\.create_plot\(\)# matplotlib$/);

    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    // The confirmed data has a plot here: the composer refines, `.start_over()` quiet beside, and
    // the status line names the data the plot was made from.
    expect(composerButtons()).toEqual(['.start_over()']);
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · data fits · 2 rows · 2 columns · version 1$/
    );
    expect(screen.getByRole('button', { name: 'Start over' })).toHaveAccessibleDescription(
      'new from the catalogue plot; keeps your remembered decisions step 2 of 2 · data fits · 2 rows · 2 columns · version 1'
    );

    // The thread names the quiet button as it read, not the action it sends.
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Start over' }), { detail: 1 });
    await waitFor(() => expect(lastAction()).toHaveTextContent(/^❯\.start_over\(\)# matplotlib$/));
    // The status line at the frame's foot always stands: the run's words take the data's place.
    expect(screen.getByRole('button', { name: 'Stop' })).toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · plotting… \.stop\(\) to cancel$/
    );
    releaseTurn?.();
    await turnEnded();
  });

  it("goes back to step 1 with the dropdowns the turn's done reports, .create_plot() filled again", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.getByLabelText(/^x/)).toHaveValue('hours');

    // Text after the plot goes as a turn, whatever it asks for.
    sendFromComposer('swap x and y');
    expect(await screen.findByText('Swapped.')).toBeInTheDocument();
    await turnEnded();
    // The binding change dropped the confirmation: the plot button is the filled CTA again,
    // although the library has a plot, and it makes the next version from the data as shown.
    const create = screen.getByRole('button', { name: 'Create plot' });
    expect(create).toBeEnabled();
    expect(composerButtons()).toEqual(['.create_plot()']);
    expect(screen.queryByRole('button', { name: 'Start over' })).not.toBeInTheDocument();
    expect(create).toHaveAccessibleDescription(
      'back to step 1 of 2 · bindings changed · check them above, then .create_plot() new from the catalogue plot; keeps your remembered decisions'
    );
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'check again · 2 rows · 2 columns · version 1'
    );
    // The root's binding change dropped the confirmation: the step line says so, and only it.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · bindings changed · check them above, then .create_plot()'
    );
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
    // The paste opens the thread, its card follows, and the summary needs no line of its own.
    expect(thread.firstElementChild).toHaveTextContent(/^❯▤ table · 3 lines · \d+ B$/);
    expect(thread).not.toHaveTextContent('.summarize_data()');
    await turnEnded();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or say what the first plot should do'
    );

    // A correction in words, before the plot: the card shows it in place. `.send()` comes with
    // the text, and sends a turn without confirming anything.
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'das ist prozent' } });
    const send = screen.getByRole('button', { name: '.send()' });
    expect(composerButtons()).toEqual(['.send()', '.create_plot()']);
    await waitFor(() => expect(send).toBeEnabled());
    fireEvent.click(send);
    const change = await screen.findByTestId('data-change');
    await turnEnded();
    expect(within(change).getByText('# changed · version 2')).toBeInTheDocument();
    expect(within(change).getByText(PREPARED.changes[0])).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    expect(composerButtons()).toEqual(['.create_plot()']);
    // Nothing was confirmed yet, so nothing was lost.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    const create = screen.getByRole('button', { name: 'Create plot' });
    await waitFor(() => expect(create).toBeEnabled());
    fireEvent.click(create);
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.getByTestId('data-summary')).toHaveTextContent('version 2');
    expect(screen.queryByTestId('data-change')).not.toBeInTheDocument();

    // The change and its `.undo()` are one `.show()` away; an undo is step 1 again.
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    const undo = within(screen.getByTestId('data-change')).getByRole('button', { name: '.undo()' });
    expect(undo).toBeEnabled();
    fireEvent.click(undo);
    expect(await screen.findByText('# undone · back to version 1')).toBeInTheDocument();
    expect(screen.getByTestId('data-summary')).toHaveTextContent('check again');
    // One line says what to do, the step line above the composer; no notice repeats it above.
    expect(lossNotice()).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · data changed · check it above, then plot the new data'
    );
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    // The undone data with a plot here: the filled CTA again, named for the data that changed.
    expect(composerButtons()).toEqual(['plot the new data']);
    expect(screen.getByRole('button', { name: 'Plot the new data' })).toBeEnabled();
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

    // The thread names the button as it read: the plot of the new data, not `.create_plot()`.
    fireEvent.click(screen.getByRole('button', { name: 'Plot the new data' }), { detail: 1 });
    await waitFor(() => expect(lastAction()).toHaveTextContent(/^❯plot the new data# matplotlib$/));
    await turnEnded();
  });

  it('sends a pasted formula to the chat, whose table becomes version 1', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    const textbox = await screen.findByLabelText('Message');
    // Without data the one box names the ways in: a table, a file, example data or a curve; the
    // how-to paragraph under the card is gone (2026-11-02).
    expect(textbox).toHaveAttribute(
      'placeholder',
      'paste a table, drop a file, or ask for example data or a curve'
    );
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
    expect(within(change).getByText('# changed · version 1')).toBeInTheDocument();
    expect(within(change).getByText(GENERATED.changes[0])).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toHaveValue('x');
    expect(screen.getByRole('cell', { name: '-1.2246468e-16' })).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    await turnEnded();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await waitFor(() => expect(create).toBeEnabled());
    fireEvent.click(create);
    await screen.findByTestId('data-pinned');
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
  });

  it('collapses the confirmed data into a pinned header that .show() opens and .hide() closes', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    const show = screen.getByRole('button', { name: 'Show the data' });
    expect(show).toHaveTextContent('.show()');
    expect(show).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(show);
    const hide = screen.getByRole('button', { name: 'Hide the data' });
    expect(hide).toHaveTextContent('.hide()');
    expect(hide).toHaveAttribute('aria-expanded', 'true');
    expect(hide).toHaveAttribute('aria-controls', 'agent-data-card');
    const card = within(screen.getByTestId('data-card'));
    expect(card.getByText(/a change here takes the data back to step 1/)).toBeInTheDocument();
    expect(card.getByRole('cell', { name: '52' })).toBeInTheDocument();
    expect(card.getByLabelText(/^x/)).toHaveValue('hours');
    // Looking is no change: the data stays confirmed, and step 2 stays.
    expect(currentStep()).toBe(2);
    expect(screen.getByRole('button', { name: 'Start over' })).toBeEnabled();

    fireEvent.click(hide);
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Show the data' })).toBeInTheDocument();
  });

  it('goes back to step 1 with the card open when a binding changes in step 2', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });

    const create = await screen.findByRole('button', { name: 'Create plot' });
    // The header stays, now in step 1's words, and leads back to the open card.
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'check again · 2 rows · 2 columns · version 1'
    );
    expect(screen.getByRole('button', { name: 'Go to the data' })).toBeInTheDocument();
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(currentStep()).toBe(1);
    expect(composerButtons()).toEqual(['.create_plot()']);
    // The loss is named once, right above the plot button, and no notice in the thread repeats it.
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · bindings changed · check them above, then .create_plot()'
    );
    expect(lossNotice()).not.toBeInTheDocument();

    // Back and forth: the confirmation is gone already, and the step line still names it.
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'score' } });
    await waitFor(() => expect(screen.getByLabelText(/^y/)).toBeEnabled());
    expect(screen.getByTestId('data-step')).toHaveTextContent('bindings changed');

    // One click takes the data again: the card collapses with it, and the row's reason goes
    // with the step.
    await waitFor(() => expect(create).toBeEnabled());
    fireEvent.click(create);
    expect(await screen.findByTestId('data-pinned')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByTestId('data-card')).not.toBeInTheDocument());
    expect(screen.getByTestId('data-summary')).toHaveTextContent('data fits');
    await turnEnded();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(currentStep()).toBe(2);
    expect(screen.getByTestId('data-step')).not.toHaveTextContent('bindings changed');
  });

  it('names the loss for the data the card shows after it, never for a new paste', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });
    await waitFor(() => expect(screen.getByLabelText(/^y/)).toBeEnabled());
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · bindings changed · check them above, then .create_plot()'
    );

    // A data request after the loss: the step line names the change the preview shows.
    sendFromComposer('read score as prozent');
    expect(await screen.findByText('I read score as numbers.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'back to step 1 of 2 · data changed · check it above, then plot the new data'
    );

    // A new paste is data nobody confirmed: plain step 1.
    await attachAndSend('hours,score\n3,70\n4,80\n');
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'step 1 of 2 · check the preview and the bindings above, then .create_plot()'
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
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
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

    // This library has a plot: the composer refines, and starting over is one quiet click
    // that says what it does, unlike `.send()` beside it.
    expect(screen.getByRole('article', { name: 'Plot version 1' })).toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask for a change, e.g. log scale on y'
    );
    // `.send()` only with text in the box.
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver).toBeEnabled();
    expect(startOver).toHaveTextContent('.start_over()');
    expect(startOver).toHaveAccessibleDescription(
      expect.stringContaining('new from the catalogue plot; keeps your remembered decisions')
    );
    expect(screen.getByTestId('data-pinned')).toBeInTheDocument();
  });

  it('goes back to step 1 on a data request after the plot, with the header leading to the card', async () => {
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
      expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();

      // A change to the data asked for below the plot, with the card collapsed.
      sendFromComposer('das ist prozent');
      const change = await screen.findByTestId('data-change');
      await turnEnded();
      expect(within(change).getByText('# changed · version 2')).toBeInTheDocument();
      expect(within(change).getByRole('button', { name: '.undo()' })).toBeEnabled();
      expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
      expect(currentStep()).toBe(1);
      // Step 1 again with a plot here: the filled CTA again, in the place of the quiet
      // `.start_over()`, named for what it does now: the next version from the changed data.
      expect(composerButtons()).toEqual(['plot the new data']);
      // The step line alone says it: no notice right above it in the thread.
      expect(lossNotice()).not.toBeInTheDocument();
      expect(screen.getByTestId('data-step')).toHaveTextContent(
        'back to step 1 of 2 · data changed · check it above, then plot the new data'
      );
      // The header stays pinned in view and leads to the card's top, far above.
      expect(screen.getByTestId('data-summary')).toHaveTextContent(
        'check again · 2 rows · 2 columns · version 2'
      );
      scroll.mockClear();
      fireEvent.click(screen.getByRole('button', { name: 'Go to the data' }));
      expect(scroll.mock.contexts).toEqual([screen.getByTestId('data-card')]);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });

      // One click: the changed data confirmed, then a new version from the catalogue plot.
      const create = screen.getByRole('button', { name: 'Plot the new data' });
      await waitFor(() => expect(create).toBeEnabled());
      fireEvent.click(create);
      await waitFor(() => expect(screen.getAllByText('Here is your plot.')).toHaveLength(2));
      await turnEnded();
      expect(confirmAndTurns().slice(-2)).toEqual(['confirm', 'create_plot']);
      expect(composerButtons()).toEqual(['.start_over()']);
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
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'decide on the table first: .use() or .discard()'
    );
    // The plot button waits for the decision, and the line above the composer says so.
    const create = screen.getByRole('button', { name: 'Create plot' });
    expect(create).toBeDisabled();
    expect(create).toHaveAccessibleDescription(
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
    expect(screen.getByTestId('data-summary')).toHaveTextContent('data fits');
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
    await waitFor(() => expect(create).toBeEnabled());
    create.focus();
    holdNextTurn = true;

    // Enter on the focused button: a click with `detail` 0. The focus continues in the
    // box, and `.stop()` is a button of its own, not the one that had the focus.
    fireEvent.click(create, { detail: 0 });
    const box = screen.getByLabelText('Message');
    expect(box).toHaveFocus();
    const stop = await screen.findByRole('button', { name: 'Stop' });
    expect(stop).not.toBe(create);
    expect(stop).not.toHaveFocus();
    fireEvent.keyDown(box, { key: 'Enter' });

    await waitFor(() => expect(releaseTurn).not.toBeNull());
    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm', 'create_plot']);
    expect(agentCalls().some(([input]) => String(input).endsWith('/cancel'))).toBe(false);
    expect(box).toHaveFocus();
  });

  it("holds back the composer's plot button while a parse runs", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver).toBeEnabled();

    await attachAndSend('slow,data\n1,2\n');
    await waitFor(() => expect(releaseParse).not.toBeNull());
    expect(startOver).toBeDisabled();

    // A new parse is new data: step 1 again, with the plot button filled for it and named so.
    releaseParse?.();
    expect(await screen.findByRole('button', { name: 'Plot the new data' })).toBeInTheDocument();
    expect(currentStep()).toBe(1);
  });

  it('offers a reload when the session open got no answer', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    sessionStorage.setItem('anyplot.debugAuthReloaded', '1'); // this tab already reloaded once
    stubFetch();
    const answered = fetchMock as unknown as (input: string, init?: RequestInit) => Response;
    // Every BFF call meets the Access redirect; the public catalogue still answers.
    fetchMock = vi.fn(async (input: string, init: RequestInit = {}) => {
      if (String(input).includes('/debug/agent/')) throw new TypeError('Failed to fetch');
      return answered(input, init);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderAt(PAGE);
    expect(await screen.findByText('error · unreachable')).toBeInTheDocument();
    // The error stands inside the chat's frame, below its header row.
    expect(screen.getByRole('region', { name: 'Chat' })).toContainElement(
      screen.getByRole('alert')
    );
    expect(screen.getByRole('button', { name: 'reload to sign in again' })).toBeInTheDocument();
    sessionStorage.clear();
  });
});

describe('AgentChatPage catalogue plot', () => {
  it('shows the catalogue plot beside the title in the library in use, and opens it large', async () => {
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

  it("lists the spec's roles behind the ⓘ after the title, as the session's open names them", async () => {
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
              ...DATASET.roles,
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

    expect(await expectedColumnsShown()).toEqual([
      'x (numeric) · x values',
      'y (numeric) · y values',
      'series (categorical, optional) · one colour per group',
    ]);
  });

  it("falls back to the spec's data bullets, without the meta lines, when the open names no roles", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    expect(await expectedColumnsShown()).toEqual([
      'x (numeric) - Independent variable values plotted on the horizontal axis',
      'y (numeric) - Dependent variable values plotted on the vertical axis',
    ]);
  });

  it('records an open from the spec hub', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&source=spec_hub`);
    await screen.findByLabelText('Message');
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
      library: 'matplotlib',
      source: 'spec_hub',
      spec: 'scatter-basic',
    });
  });

  it('records an open from the plot of the day, then drops the source', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&source=plot_of_the_day`);
    await screen.findByLabelText('Message');
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
      library: 'matplotlib',
      source: 'plot_of_the_day',
      spec: 'scatter-basic',
    });
    await waitFor(() => expect(screen.getByTestId('location')).not.toHaveTextContent('source='));
    expect(screen.getByTestId('location')).toHaveTextContent(PAGE);
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
    // Step 2: the card waits behind the pinned header.
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();

    await attachAndSend('hours,score\n3,70\n4,80\n');
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    const stub = screen.getByTestId('data-stub');
    expect(stub).toHaveTextContent('# earlier data · 2 rows · 2 columns · replaced below');
    const [first, second] = screen.getAllByTestId('paste-item');
    const card = screen.getByTestId('data-card');
    // The first paste, its stub, the plot of that data, then the new paste and its card.
    expect(follows(first, stub)).toBe(true);
    expect(follows(stub, screen.getByText('Here is your plot.'))).toBe(true);
    expect(follows(screen.getByText('Here is your plot.'), second)).toBe(true);
    expect(follows(second, card)).toBe(true);
    // New data nobody confirmed: step 1, its card open.
    expect(currentStep()).toBe(1);
  });

  it("opens the card at its place in the thread from the pinned header's .show(), and scrolls to it", async () => {
    const { scroll, done } = spyScroll();
    try {
      localStorage.setItem(ADMIN_HINT_KEY, '1');
      renderAt(PAGE);
      await parseAndPlot();
      scroll.mockClear();
      fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
      const card = await screen.findByTestId('data-card');
      expect(screen.getByRole('log', { name: 'Conversation' })).toContainElement(card);
      expect(follows(screen.getByTestId('paste-item'), card)).toBe(true);
      // Inside the polite log, the card's own changes are no news to read out.
      expect(card).toHaveAttribute('aria-live', 'off');
      const calls = scroll.mock.contexts.flatMap((context, index) =>
        context === card ? [scroll.mock.calls[index][0]] : []
      );
      expect(calls).toEqual([{ behavior: 'smooth', block: 'start' }]);
    } finally {
      done();
    }
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
  it('offers example data above the composer without data, as an action, working until it arrives', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    const line = screen.getByTestId('example-data');
    expect(line).toHaveTextContent('# no data at hand?.example_data()');

    holdNextTurn = true;
    // A key press (a click without a pointer) goes on in the message box: the button gives way.
    fireEvent.click(within(line).getByRole('button', { name: 'Make example data' }));

    // The line steps aside while the turn runs: the thread says it once, beside the loader.
    const pending = await screen.findByTestId('pending-reply');
    expect(pending).toHaveTextContent(/^making example data$/);
    expect(within(pending).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(screen.getAllByText(/making example data/)).toHaveLength(1);
    expect(screen.queryByTestId('example-data')).not.toBeInTheDocument();
    // Its room stays, empty, so the composer below it does not jump.
    expect(screen.getByTestId('example-data-room')).toBeEmptyDOMElement();
    expect(screen.getByLabelText('Message')).toHaveFocus();
    expect(turnBodies()).toEqual([{ action: 'example_data' }]);
    // The thread names the page's own turn and holds the assistant's slot.
    expect(screen.getByRole('log', { name: 'Conversation' })).toHaveTextContent('.example_data()');

    releaseTurn?.();
    expect(await screen.findByText(EXAMPLE_REPLY)).toBeInTheDocument();
    await turnEnded();
    // The data is there: the line goes, the card shows the table, and nothing set a language.
    expect(screen.queryByTestId('example-data')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toHaveValue('x');
    expect(screen.queryByText(/reply language/)).not.toBeInTheDocument();
  });

  it('comes back when the turn brought no data, and waits while another turn runs', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    holdNextTurn = true;
    sendFromComposer('what is the mean score?');
    const button = await screen.findByRole('button', { name: 'Make example data' });
    expect(button).toBeDisabled();
    releaseTurn?.();
    await turnEnded();
    expect(screen.getByRole('button', { name: 'Make example data' })).toBeEnabled();
  });

  it('steps aside while a table waits in the box, and is gone once a paste stored data', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    const box = await screen.findByLabelText('Message');
    await waitFor(() => expect(box).toBeEnabled());
    expect(screen.getByTestId('example-data')).toBeInTheDocument();
    fireEvent.paste(box, {
      clipboardData: { files: [], getData: () => 'hours,score\n1.5,52\n2.0,58\n' },
    });
    // The attachment is data at hand: example data would only replace it.
    expect(screen.queryByTestId('example-data')).not.toBeInTheDocument();
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();

    expect(screen.queryByTestId('example-data')).not.toBeInTheDocument();
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
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndPlot();
    expect(unload()).toBe(true);

    // The library menu's `all` writes the query on the same path: nothing to ask.
    await pickInMenu('All libraries');
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('all=1'));
    expect(confirm).not.toHaveBeenCalled();

    // The back link to the plot, declined: the chat and its session stay.
    fireEvent.click(backLink());
    await waitFor(() => expect(confirm).toHaveBeenCalledWith(LEAVE_TEXT));
    expect(screen.getByTestId('data-pinned')).toBeInTheDocument();
    expect(deletes()).toHaveLength(0);

    // Agreed: the page goes, and the session with it.
    confirm.mockReturnValue(true);
    fireEvent.click(backLink());
    await waitFor(() => expect(screen.queryByTestId('data-pinned')).not.toBeInTheDocument());
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

    const pending = await screen.findByTestId('pending-reply');
    expect(pending).toHaveTextContent(/^summarizing your data$/);
    expect(within(pending).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(lastInThread()).toBe(pending);
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(
      /^# bindings — wait while the assistant works$/
    );
    // One loader, in the thread: the bindings heading says why without motion of its own.
    expect(screen.getAllByTestId('loader-spinner')).toHaveLength(1);
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
    // The plot button waits in its place at the composer's end, beside `.stop()`.
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeDisabled();
    expect(composerButtons()).toEqual(['.stop()', '.create_plot()']);
    // One indicator: a turn without pipeline steps mounts no progress timeline.
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Stop' })).toBeInTheDocument();

    releaseTurn?.();
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(
      /^# bindings — which column plays which role$/
    );
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
  });

  it('puts an in-progress line in the thread for a question, and leaves a plot run to the timeline', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();

    holdNextTurn = true;
    sendFromComposer('what is the mean score?');
    const pending = await screen.findByTestId('pending-reply');
    expect(pending).toHaveTextContent(/^working on your message$/);
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    releaseTurn?.();
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
    await turnEnded();

    // `.create_plot()` shows its path in the timeline from the start, with the loader beside
    // it; the thread adds nothing.
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByRole('table', { name: 'Progress' })).toBeInTheDocument();
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
    expect(screen.getAllByTestId('loader-spinner')).toHaveLength(1);
    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.queryByTestId('loader-spinner')).not.toBeInTheDocument();
  });

  it('shows one queue position, out of the flow for a text turn and in the timeline for a plot run', async () => {
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

    // A question waits with the thread's in-progress line: the badge names the position, beside
    // that line and out of the flow, so it moves nothing as it comes and goes.
    sendFromComposer('what is the mean score?');
    const badge = await screen.findByTestId('queue-counter');
    expect(badge).toHaveTextContent('queue 2/3');
    expect(badge).toHaveStyle({ position: 'absolute' });
    expect(screen.getByTestId('pending-reply')).toBeInTheDocument();
    // The wait ends before the reply: the badge goes, the in-progress line stays.
    act(() => push?.([['status', { step: 'started' }]]));
    await waitFor(() => expect(screen.queryByTestId('queue-counter')).not.toBeInTheDocument());
    expect(screen.getByTestId('pending-reply')).toBeInTheDocument();
    act(() => finish?.());
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();

    // A plot run names its position in the timeline's first row, and nowhere else.
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    const grid = await screen.findByRole('table', { name: 'Progress' });
    expect(await within(grid).findByText('queued · 2 of 3')).toBeInTheDocument();
    expect(screen.queryByTestId('queue-counter')).not.toBeInTheDocument();
    expect(screen.getAllByText(/queue/)).toHaveLength(1);
    // Out of the queue before its first step, the run is starting.
    act(() => push?.([['status', { step: 'started' }]]));
    expect(await within(grid).findByText('starting…')).toBeInTheDocument();
    expect(screen.queryByText(/queue/)).not.toBeInTheDocument();
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
  it('shows .send() only while the box holds text', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    // No data, an empty box: nothing to send, and the status line names only the step.
    expect(composerButtons()).toEqual([]);
    expect(screen.getByTestId('data-step')).toHaveTextContent(/^>>> step 1 of 2 · your data$/);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'sin(x) please' } });
    expect(composerButtons()).toEqual(['.send()']);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: '   ' } });
    expect(composerButtons()).toEqual([]);

    // With data the plot button stands alone until there is text, then `.send()` before it.
    await parseAndSummarize();
    expect(composerButtons()).toEqual(['.create_plot()']);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale' } });
    expect(composerButtons()).toEqual(['.send()', '.create_plot()']);
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
    expect(create).toBeDisabled();
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

  it('offers all once the lists are in, and .plot_all() confirms the table, then plots it everywhere', async () => {
    const base = baseFetch();
    // The status answer waits: until it is in, the libraries and the limit are fallbacks.
    let releaseStatus!: () => void;
    const status = new Promise<void>(resolve => (releaseStatus = resolve));
    fetchMock.mockImplementation((input: string, init?: RequestInit) =>
      input.endsWith('/debug/agent/status')
        ? status.then(() =>
            json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true, user_max_runs: 4 })
          )
        : base(input, init)
    );
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    let menu = await openLibraryMenu();
    expect(within(menu).queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    await closeLibraryMenu();
    releaseStatus();

    menu = await openLibraryMenu();
    const all = await within(menu).findByRole('button', { name: 'All libraries' });
    expect(all).toHaveTextContent('all libraries');
    expect(within(menu).getByRole('group', { name: 'Admin' })).toContainElement(all);
    expect(all).toHaveAttribute('aria-pressed', 'false');
    expect(within(menu).getByRole('button', { name: 'matplotlib' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    await closeLibraryMenu();
    expect(screen.queryByRole('button', { name: 'Plot in all libraries' })).not.toBeInTheDocument();

    // Pressed, `all` is what the chip names, and the composer's create action plots everywhere.
    await pickInMenu('All libraries');
    expect(libraryChip()).toHaveTextContent(/^all 2 libraries ▾$/);
    expect(libraryChip()).toHaveAccessibleName('Library: all 2 libraries. Change');
    menu = await openLibraryMenu();
    expect(within(menu).getByRole('button', { name: 'All libraries' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    const own = within(menu).getByRole('button', { name: 'matplotlib' });
    expect(own).toHaveAttribute('aria-pressed', 'false');
    expect(own).toBeEnabled();
    await closeLibraryMenu();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    // In step 1 `.plot_all()` is the filled CTA, the chat about the data goes on.
    const plotAll = plotAllButton();
    expect(plotAll).toHaveTextContent('.plot_all()');
    expect(plotAll).toBeEnabled();
    expect(composerButtons()).toEqual(['.plot_all()']);
    // The line leads to the button that shows: `.plot_all()`, not the `.create_plot()` it replaces.
    expect(plotAll).toHaveAccessibleDescription(
      'step 1 of 2 · check the preview and the bindings above, then .plot_all()'
    );
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.queryByTestId('plot-all-hint')).not.toBeInTheDocument();

    // The click confirms the data first: the copy route needs confirmed data.
    fireEvent.click(plotAll, { detail: 1 });
    const panel = await screen.findByRole('region', { name: 'All libraries' });
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm']);
    // The fan-out takes no text: in step 2 the message box waits, and the line says why.
    const line =
      '# step 2 — plot the table as it is in all 2 libraries at once · turn all off to chat';
    const box = screen.getByLabelText('Message');
    expect(box).toBeDisabled();
    expect(box).toHaveAccessibleDescription(line);
    expect(box).toHaveAttribute(
      'placeholder',
      'all libraries: the table goes as it is · turn all off to chat'
    );
    expect(plotAllButton()).toHaveAccessibleDescription(expect.stringContaining(line));
    expect(
      within(panel)
        .getAllByRole('article')
        .map(card => card.getAttribute('aria-label'))
    ).toEqual(['matplotlib', 'seaborn']);
    expect(within(panel).getByText(/at most 4 at a time/)).toBeInTheDocument();
    // A pointer click moves no focus.
    expect(panel).not.toHaveFocus();
    // While the panel is open, nothing starts another fan-out or changes the library, whose
    // session the panel's sessions copy their data from; `all` stays pressed.
    expect(plotAllButton()).toBeDisabled();
    expect(libraryChip()).toBeDisabled();
    expect(libraryChip()).toHaveTextContent(/^all 2 libraries ▾$/);

    // `.close()` goes with the panel: the focus returns to `.plot_all()`, which opened it.
    const close = within(panel).getByRole('button', { name: 'Close all libraries' });
    close.focus();
    fireEvent.click(close);
    expect(screen.queryByRole('region', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(plotAllButton()).toBeEnabled();
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
    await pickInMenu('All libraries');
    const plotAll = plotAllButton();
    await waitFor(() => expect(plotAll).toBeEnabled());

    fireEvent.click(plotAll, { detail: 1 });
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ref r-a'));
    // No panel, no copied session, and step 1 holds with `.plot_all()` ready for a retry.
    expect(screen.queryByRole('region', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(confirmAndTurns()).toEqual(['summarize_data', 'confirm']);
    expect(agentCalls().some(([input]) => String(input).endsWith('/dataset/copy'))).toBe(false);
    expect(currentStep()).toBe(1);
    expect(plotAllButton()).toBeEnabled();
  });

  it('shows no all pill when the page has one library', async () => {
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
    expect(within(menu).queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    await closeLibraryMenu();
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
  });

  it('turns all off from any library in the menu: the own one only that, another switches', async () => {
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

    // `all` itself is a toggle: a second pick turns it off again.
    await pickInMenu('All libraries');
    expect(screen.getByLabelText('Message')).toBeDisabled();
    await pickInMenu('All libraries');
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);
    expect(screen.getByRole('button', { name: 'Start over' })).toHaveTextContent('.start_over()');
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).not.toHaveAccessibleDescription();

    await pickInMenu('All libraries');
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

    await pickInMenu('All libraries');
    await pickInMenu('seaborn');
    await waitFor(() =>
      expect(screen.getByTestId('location')).toHaveTextContent('library=seaborn')
    );
    expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/);
    expect(screen.getByTestId('location')).not.toHaveTextContent('all=1');
  });

  it('leaves the chat about the data usable with all pressed, before data and in step 1', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await screen.findByLabelText('Message');

    // Without data: nothing to plot yet, and the box asks for a curve as without `all`.
    await pickInMenu('All libraries');
    expect(libraryChip()).toHaveTextContent(/^all \d+ libraries ▾$/);
    expect(screen.queryByRole('button', { name: 'Plot in all libraries' })).not.toBeInTheDocument();
    const box = screen.getByLabelText('Message');
    expect(box).toBeEnabled();
    expect(box).toHaveAttribute(
      'placeholder',
      'paste a table, drop a file, or ask for example data or a curve'
    );
    expect(box).not.toHaveAccessibleDescription();

    // Step 1: `.plot_all()` is the action, and a question about the data goes: the box waits
    // only once the data is confirmed.
    await parseAndSummarize();
    expect(currentStep()).toBe(1);
    expect(composerButtons()).toEqual(['.plot_all()']);
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

    await pickInMenu('All libraries');
    // Computed data has no paste, and `.plot_all()` needs none: it is the action, with no hint.
    const plotAll = plotAllButton();
    expect(plotAll).toBeEnabled();
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
    await pickInMenu('All libraries');
    fireEvent.click(plotAllButton(), { detail: 1 });
    const panel = await screen.findByRole('region', { name: 'All libraries' });

    // Opening the card is only a look: it opens, but nothing in it changes the data.
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    const card = screen.getByRole('region', { name: 'Your data' });
    const line = '# the data waits while all libraries plot it · .close() the panel to change it';
    expect(within(card).getByTestId('data-lock')).toHaveTextContent(line);
    expect(card).toHaveAccessibleDescription(line);
    expect(within(card).getByLabelText(/^x/)).toBeDisabled();
    // A new file waits too: the panel's sessions copy this data.
    expect(screen.getByRole('button', { name: 'Attach a data file' })).toBeDisabled();

    fireEvent.click(within(panel).getByRole('button', { name: 'Close all libraries' }));
    expect(screen.queryByTestId('data-lock')).not.toBeInTheDocument();
    const reopened = screen.getByRole('region', { name: 'Your data' });
    expect(reopened).not.toHaveAccessibleDescription();
    expect(screen.getByRole('button', { name: 'Attach a data file' })).toBeEnabled();
    expect(within(reopened).getByLabelText(/^x/)).toBeEnabled();
  });

  it('posts the paste again in every library while the server has no copy', async () => {
    fanOutSessions(() => json(404, { detail: 'not_found', ref: 'r-404' }));
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndSummarize();
    await pickInMenu('All libraries');
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
    renderAt('/debug/agent?spec=scatter-basic&library=matplotlib&language=javascript');
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

  it('keeps all in the URL, and presses it again from there once the lists are in', async () => {
    let releaseStatus!: () => void;
    threeLibraries(new Promise<void>(resolve => (releaseStatus = resolve)));
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const first = renderAt(PAGE);
    releaseStatus();
    await screen.findByLabelText('Message');
    expect(query().has('all')).toBe(false);

    await pickInMenu('All libraries');
    await waitFor(() => expect(query().get('all')).toBe('1'));
    await pickInMenu('All libraries');
    await waitFor(() => expect(query().has('all')).toBe(false));
    await pickInMenu('All libraries');
    await waitFor(() => expect(query().get('all')).toBe('1'));
    const reloaded = location();
    first.unmount();

    // The reload: until the lists are in, `all` is not offered, and the URL keeps it.
    threeLibraries(new Promise<void>(resolve => (releaseStatus = resolve)));
    renderAt(reloaded);
    await screen.findByLabelText('Message');
    let menu = await openLibraryMenu();
    expect(within(menu).queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    await closeLibraryMenu();
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);
    expect(query().get('all')).toBe('1');
    releaseStatus();
    await waitFor(() => expect(libraryChip()).toHaveTextContent(/^all 3 libraries ▾$/));
    menu = await openLibraryMenu();
    expect(within(menu).getByRole('button', { name: 'All libraries' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    expect(within(menu).getByRole('button', { name: 'matplotlib' })).toHaveAttribute(
      'aria-pressed',
      'false'
    );
    await closeLibraryMenu();
    expect(query().get('all')).toBe('1');
  });

  it('drops all from the URL: a library picked, and a page that offers none', async () => {
    threeLibraries();
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const first = renderAt(`${PAGE}&all=1`);
    await waitFor(() => expect(libraryChip()).toHaveTextContent(/^all 3 libraries ▾$/));
    await waitFor(() => expect(libraryChip()).toBeEnabled());

    // Another library switches and turns `all` off: the URL names the new library, without `all`.
    await pickInMenu('seaborn');
    await waitFor(() => expect(query().get('library')).toBe('seaborn'));
    expect(query().has('all')).toBe(false);
    expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/);
    first.unmount();

    // One library: no `all` to press, so the URL does not keep it.
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation((input: string, init?: RequestInit) =>
      input.endsWith('/debug/agent/status')
        ? Promise.resolve(json(200, { libraries: ['matplotlib'], enabled: true }))
        : base(input, init)
    );
    renderAt(`${PAGE}&all=1`);
    await waitFor(() => expect(query().has('all')).toBe(false));
    expect(libraryChip()).toHaveTextContent(/^matplotlib ▾$/);
    expect(query().get('library')).toBe('matplotlib');
  });
});

describe('AgentChatPage service pause', () => {
  /** The status answer as `stubFetch` gives it, plus `extra`. */
  function statusWith(extra: Record<string, unknown>) {
    const base = fetchMock.getMockImplementation() as (
      input: string,
      init?: RequestInit
    ) => Promise<Response>;
    fetchMock.mockImplementation((input: string, init?: RequestInit) =>
      input.endsWith('/debug/agent/status')
        ? Promise.resolve(
            json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true, ...extra })
          )
        : base(input, init)
    );
  }

  it('says before the user types that the whole chat paused, until when in their time', async () => {
    const resetsAt = new Date(Date.now() + 3_600_000).toISOString();
    statusWith({ paused: true, resets_at: resetsAt });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);

    const note = await screen.findByTestId('service-paused');
    expect(note).toHaveAttribute('role', 'note');
    expect(note).toHaveTextContent(`# ${servicePausedText(resetsAt)}`);
    // `/status` is the same for everyone: a user whose own budget is spent too must not read otherwise.
    expect(note).not.toHaveTextContent('your own limit');
    // The composer stays: the note may go stale at midnight, the server decides each turn.
    expect(screen.getByLabelText('Message')).toBeInTheDocument();
  });

  it('shows no note while the service runs, nor for a reset already past', async () => {
    statusWith({ paused: false, resets_at: new Date(Date.now() + 3_600_000).toISOString() });
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { unmount } = renderAt(PAGE);
    await screen.findByLabelText('Message');
    await waitFor(() =>
      expect(agentCalls().some(([input]) => pathOf(input).endsWith('/status'))).toBe(true)
    );
    expect(screen.queryByTestId('service-paused')).not.toBeInTheDocument();
    unmount();

    statusWith({ paused: true, resets_at: new Date(Date.now() - 1_000).toISOString() });
    renderAt(PAGE);
    await screen.findByLabelText('Message');
    expect(screen.queryByTestId('service-paused')).not.toBeInTheDocument();
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

  const memoryList = () => screen.getByRole('region', { name: /remembered/ });

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
    // The run's decisions stand above the composer.
    expect(await screen.findByRole('region', { name: /remembered · 2 decisions/ })).toBeVisible();
    const turns = turnBodies().length;

    await pickInMenu('seaborn');
    // Browsing costs nothing: the switch runs no turn.
    const carry = await screen.findByTestId('carry-plot');
    expect(turnBodies()).toHaveLength(turns);
    expect(carry).toHaveTextContent('plot in seaborn with your 2 decisions');
    expect(carry).toHaveAccessibleName('plot in seaborn with your 2 decisions');
    // Seaborn has no plot yet: the offer is the step's filled action at the composer's end, and
    // the quiet plot from the catalogue code, `.start_over()`, stands before it: a second
    // `.create_plot()` there read as the same click.
    expect(carry).toHaveAttribute('type', 'button');
    expect(composerButtons()).toEqual(['.start_over()', 'plot in seaborn with your 2 decisions']);
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · plot in seaborn with your 2 decisions, or say/
    );
    expect(carry).toHaveAccessibleDescription(
      'step 2 of 2 · plot in seaborn with your 2 decisions, or say first what it should do differently'
    );
    const fresh = screen.getByRole('button', { name: 'Start over' });
    expect(fresh).toHaveTextContent('.start_over()');
    expect(fresh).toHaveAccessibleDescription(
      expect.stringContaining('keeps your remembered decisions')
    );
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();

    fireEvent.click(carry, { detail: 1 });
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ action: 'carry_plot' });
    const thread = screen.getByRole('log', { name: 'Conversation' });
    // The thread names the button as it read, never the action the page sent.
    expect(lastAction()).toHaveTextContent(/^❯plot in seaborn with your 2 decisions$/);
    expect(within(thread).queryByText(/carry_plot/)).not.toBeInTheDocument();
    // Shipped in seaborn: the offer is spent, the composer refines this plot.
    expect(screen.queryByTestId('carry-plot')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start over' })).toBeEnabled();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'a title' } });
    expect(composerButtons()).toEqual(['.start_over()', '.send()']);
  });

  it('confirms changed data before the carry, in the same click', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await screen.findByTestId('carry-plot');
    // A binding changed in the new library drops the confirmation the switch kept.
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });
    await waitFor(() => expect(currentStep()).toBe(1));
    const carry = screen.getByTestId('carry-plot');
    await waitFor(() => expect(carry).toBeEnabled());
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
    fireEvent.click(screen.getByRole('button', { name: '.send()' }));

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

    fireEvent.change(screen.getByRole('textbox', { name: 'Message' }), {
      target: { value: 'make it in seaborn' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.send()' }));

    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(
      await within(thread).findByText(/this plot cannot be adapted in that library/)
    ).not.toHaveTextContent('r-sw');
    await turnEnded();
    expect(turnBodies()).toHaveLength(turns + 1); // the typed turn alone: no carry run
  });

  it('sends .start_over() beside the offer as the fresh plot, which ends the offer too', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await screen.findByTestId('carry-plot');
    fireEvent.click(screen.getByRole('button', { name: 'Start over' }));
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ action: 'create_plot' });
    expect(screen.queryByTestId('carry-plot')).not.toBeInTheDocument();
  });

  it('shows .create_plot() alone after a switch whose offer carries no decisions, and carries with it', async () => {
    // Both buttons read as the same click when there is nothing to take along.
    switchRoutes({
      carry: { decisions: 0, newer: 0, target_has_plot: false, from_plot: true, offer: true },
      memory: [],
    });
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    await waitFor(() => expect(libraryChip()).toHaveTextContent(/^seaborn ▾$/));
    expect(screen.queryByTestId('carry-plot')).not.toBeInTheDocument();
    expect(composerButtons()).toEqual(['.create_plot()']);
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      /^>>> step 2 of 2 · create the plot as it is, or say first/
    );

    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();
    // The carry still runs, with the theme asked for in the library before.
    expect(lastTurn()).toEqual({ action: 'carry_plot' });
  });

  it('keeps .start_over() and .send() beside the offer in a library with an older plot; text goes as a turn', async () => {
    const routes = { carry: OFFER as unknown, memory: [LINE] };
    switchRoutes(routes);
    await plotInMatplotlib();
    await pickInMenu('seaborn');
    fireEvent.click(await screen.findByTestId('carry-plot'));
    expect(await screen.findByText('Plot 2.')).toBeInTheDocument();
    await turnEnded();

    // Back to matplotlib, whose plot misses a newer decision: the server offers the carry again.
    routes.carry = { decisions: 1, newer: 1, target_has_plot: true, from_plot: true, offer: true };
    await pickInMenu('matplotlib');
    const carry = await screen.findByTestId('carry-plot');
    expect(carry).toHaveTextContent('plot in matplotlib with your 1 decision');
    expect(carry).toHaveAttribute('type', 'button');
    expect(screen.getByRole('button', { name: 'Start over' })).toBeEnabled();
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'dashed line' } });
    const send = screen.getByRole('button', { name: '.send()' });
    expect(send).toBeEnabled();
    fireEvent.click(send);
    expect(await screen.findByText('Plot 3.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ text: 'dashed line' });
    // The typed change shipped in matplotlib: that ends the offer as well.
    expect(screen.queryByTestId('carry-plot')).not.toBeInTheDocument();
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
    expect(screen.queryByTestId('carry-plot')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveTextContent('.create_plot()');
    expect(screen.queryByRole('region', { name: /remembered/ })).not.toBeInTheDocument();
  });

  it('forgets a remembered decision, and holds the list while a turn runs', async () => {
    switchRoutes({ carry: OFFER, memory: [LINE, LABEL] });
    await plotInMatplotlib();
    const list = await screen.findByRole('region', { name: /remembered · 2 decisions/ });
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
    await waitFor(() => expect(memoryList()).toHaveAccessibleName('# remembered · 1 decision'));
    expect(
      agentCalls()
        .filter(([, init]) => (init as RequestInit | undefined)?.method === 'DELETE')
        .map(([input]) => pathOf(input))
    ).toContain('/debug/agent/sessions/S1/memory/m1');
    expect(within(memoryList()).queryByText(LINE.text)).not.toBeInTheDocument();
    expect(within(memoryList()).getByText(LABEL.text)).toBeInTheDocument();
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

    // A table: no text in the box, a chip with its size, `.send()` to read it.
    expect(pasteText(TABLE)).toBe(false);
    expect(message()).toHaveValue('');
    expect(chip()).toHaveAccessibleName('Attached table, 4 lines, 33 B');
    expect(chip()).toHaveTextContent('▤ table · 4 lines · 33 B');
    expect(screen.getByTestId('composer-status')).toHaveTextContent('Attached table, 4 lines');
    expect(composerButtons()).toEqual(['×', '.send()']);
    expect(message()).toHaveAttribute('placeholder', 'add a note for this table, or press Enter');
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      'step 1 of 2 · the attached table is read when you send it: Enter or .send(), with a note if you like'
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
    fireEvent.click(screen.getByRole('button', { name: '.send()' }));
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
    // Enter tries the same table again.
    expect(screen.getByRole('button', { name: '.send()' })).toBeEnabled();
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
    screen.getByRole('button', { name: 'Attach a data file' }).focus();
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
    expect(screen.getByRole('button', { name: '.send()' })).toBeDisabled();
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
    expect(screen.getByRole('button', { name: 'Attach a data file' })).toBeDisabled();
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

  it('marks a table over the caps red and holds .send() back', async () => {
    await openChat();
    pasteText(`x,y\n${'1,2\n'.repeat(20_100)}`);
    expect(chip()).toHaveAttribute('data-status', 'over_cap');
    expect(screen.getByTestId('attachment-error')).toHaveTextContent(
      'at most 20,000 rows and 1 MB: filter first, or .open() an Excel or Parquet file (5 MB)'
    );
    expect(screen.getByRole('button', { name: '.send()' })).toBeDisabled();
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

  it('holds the plot button back while a chip waits, and asks before a reload drops it', async () => {
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
    expect(create).toBeDisabled();
    // The session holds data: the line says that the table replaces it, for good.
    expect(create).toHaveAccessibleDescription(
      'step 1 of 2 · the attached table replaces your data (2 rows, no .undo()) when you send it: Enter or .send(), with a note if you like'
    );
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
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeDisabled();
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
    expect(screen.getByRole('button', { name: 'Attach a data file' })).toBeDisabled();
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

    // Over the cap: the whole text stays, the counter turns red, `.send()` and Enter wait.
    const long = 'a'.repeat(2001);
    fireEvent.change(message(), { target: { value: long } });
    expect(message()).toHaveValue(long);
    expect(message()).not.toHaveAttribute('maxlength');
    expect(message()).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByTestId('message-counter')).toHaveTextContent('2,001 / 2,000');
    expect(screen.getByTestId('composer-status')).toHaveTextContent(
      'the message is longer than 2,000 characters'
    );
    expect(screen.getByRole('button', { name: '.send()' })).toBeDisabled();
    fireEvent.keyDown(message(), { key: 'Enter' });
    expect(turnBodies()).toHaveLength(1);
  });

  it("keeps the how-to of the data behind the ⓘ in the frame's header row, after the chips", async () => {
    await openChat();
    // The `# chat` label it stood beside is gone: the ⓘ follows the language chip, before the
    // thread, inside the frame.
    const howto = screen.getByRole('button', { name: 'How the chat takes data' });
    const follows = (first: Element, second: Element) =>
      !!(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);
    expect(screen.queryByText('# chat')).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Chat' })).toContainElement(howto);
    expect(follows(screen.getByTestId('language-chip'), howto)).toBe(true);
    expect(follows(howto, screen.getByRole('log', { name: 'Conversation' }))).toBe(true);
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
