import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AgentChatPage } from 'src/pages/AgentChatPage';
import { LEAVE_TEXT } from 'src/sections/agent-chat/messages';
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

/** Free text the server reads into a table with a model and does not store. */
const FREE_TEXT = 'Hund 7 Katze 3 und Vogel 4';
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
        implementations: [{ library_id: 'matplotlib' }, { library_id: 'seaborn' }],
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

/** Paste a table, wait for its summary and confirm it: the page is at step 2. */
async function parseAndConfirm(value = 'hours,score\n1.5,52\n2.0,58\n') {
  fireEvent.change(await screen.findByLabelText(/# your data/), { target: { value } });
  fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
  expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
  const confirm = screen.getByRole('button', { name: '.confirm()' });
  await waitFor(() => expect(confirm).toBeEnabled());
  fireEvent.click(confirm);
  await screen.findByTestId('data-pinned');
}

/** The turn in flight is over: its `done` was applied and `.stop()` gave way. */
const turnEnded = () =>
  waitFor(() => expect(screen.queryByRole('button', { name: 'Stop' })).not.toBeInTheDocument());

/** Send `text` from the composer with Enter. */
function sendFromComposer(text: string) {
  const box = screen.getByLabelText('Message');
  fireEvent.change(box, { target: { value: text } });
  fireEvent.keyDown(box, { key: 'Enter' });
}

/** In step 2, open the card and paste free text, which comes back as a table to decide on. */
async function transcribeInStep2() {
  fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
  fireEvent.change(screen.getByLabelText(/# your data/), { target: { value: FREE_TEXT } });
  fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
  await screen.findByTestId('transcription-card');
}

/**
 * The composer's quiet `.create_plot()`, which shows in step 1 too: a plain button, not
 * step 2's submitting CTA.
 */
/** The quiet create button: `.create_plot()`, or `.start_over()` once the library has a plot. */
function quietCreate(name: 'Create plot' | 'Start over' = 'Create plot') {
  const create = screen.getByRole('button', { name });
  expect(create).toHaveAttribute('type', 'button');
  return create;
}

/** The thread's last entry. */
const lastInThread = () => screen.getByRole('log', { name: 'Conversation' }).lastElementChild;

/** `scrollIntoView` as a spy: jsdom has none. Restore with `restoreScrollIntoView`. */
function stubScrollIntoView() {
  const scroll = vi.fn();
  Object.defineProperty(Element.prototype, 'scrollIntoView', {
    value: scroll,
    configurable: true,
    writable: true,
  });
  return scroll;
}

function restoreScrollIntoView() {
  delete (Element.prototype as Partial<Element>).scrollIntoView;
}

/** The step the step header marks as current. */
const currentStep = () =>
  within(screen.getByRole('list', { name: 'Steps' }))
    .getAllByRole('listitem')
    .filter(item => item.getAttribute('aria-current') === 'step')
    .map(item => item.textContent);

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
    expect(await screen.findByLabelText(/# your data/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.parse()' })).toBeInTheDocument();
    expect(analytics.trackPageview).toHaveBeenCalledWith('/debug/agent');
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
      library: 'matplotlib',
      source: 'plot_page',
      spec: 'scatter-basic',
    });
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(PAGE));
    expect(await screen.findByText('← Basic Scatter Plot')).toBeInTheDocument();
  });

  it('lets local development in without the hint', async () => {
    flags.isDev = true;
    renderAt(PAGE);
    expect(await screen.findByLabelText(/# your data/)).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith(
      'agent_open',
      expect.objectContaining({ source: 'direct' })
    );
  });

  it('explains the missing parameters instead of calling the BFF', () => {
    flags.isDev = true;
    renderAt('/debug/agent?spec=scatter-basic&library=excel');
    expect(screen.getByText(/open this page from a plot/)).toBeInTheDocument();
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
    expect(await screen.findByText('not eligible · ref r1')).toBeInTheDocument();
    // No session exists to switch, so a pick opens the page anew with its own session.
    await waitFor(() =>
      expect(screen.getByRole('link', { name: 'seaborn' })).toHaveAttribute(
        'href',
        '/debug/agent?spec=scatter-basic&library=seaborn&language=python'
      )
    );
    expect(screen.getByRole('button', { name: 'matplotlib' })).toBeDisabled();
  });

  it('walks the two steps: confirm the data, then create the plot', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    expect(await screen.findByLabelText(/# your data/)).toBeInTheDocument();
    expect(currentStep()).toEqual(['1 data']);
    expect(
      screen.getByText(/check the preview and the bindings, confirm, then/)
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    const confirm = await screen.findByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    // Step 1 shows `.create_plot()` too, the quiet one, which waits for the confirmation.
    expect(quietCreate()).toBeEnabled();
    // The data card is the thread's first turn; the summary follows it.
    const card = screen.getByTestId('data-card');
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(card.compareDocumentPosition(thread) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // The first binding setup after a paste dropped no confirmation: nothing to name.
    expect(screen.queryByTestId('confirm-lost')).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      '# step 1 — check the preview and the bindings, then confirm'
    );

    fireEvent.click(confirm);
    await screen.findByTestId('data-pinned');
    const create = screen.getByRole('button', { name: 'Create plot' });
    expect(create).toHaveAttribute('type', 'submit');
    expect(create).toBeEnabled();
    expect(currentStep()).toEqual(['·2 plot']);
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'data fits · 2 rows · 2 columns · version 1'
    );
    expect(create).toHaveAccessibleDescription(
      'data fits · 2 rows · 2 columns · version 1 # step 2 — create the plot as it is, or say first what it should do differently'
    );
    // The confirmation's button is gone with the card: the keyboard continues here.
    await waitFor(() => expect(create).toHaveFocus());
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 2: the data is confirmed; create the plot below'
    );
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_confirmed', {
      size_bucket: 'lt_1kb',
    });
    // The chat composer was usable the whole time; it is not part of the steps.
    expect(screen.getByLabelText('Message')).toBeEnabled();
  });

  it("goes back to step 1 with the dropdowns the turn's done reports", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.getByLabelText(/^x/)).toHaveValue('hours');

    // Text in step 2's box goes as a turn, whatever it asks for.
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'swap x and y' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Swapped.')).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: '.confirm()' })).toBeEnabled();
    expect(quietCreate()).toBeEnabled();
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'confirm again · 2 rows · 2 columns · version 1'
    );
    // The root's binding change dropped the confirmation: the thread says so after the reply.
    expect(lastInThread()).toHaveTextContent('# bindings changed · confirm the data again');
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      '# step 1 again — bindings changed · confirm the data again'
    );
    expect(screen.getByLabelText(/^x/)).toHaveValue('score');
    expect(screen.getByLabelText(/^y/)).toHaveValue('hours');
    expect(screen.getByText('1 data')).toHaveAttribute('aria-current', 'step');
    expect(lastTurn()).toEqual({ text: 'swap x and y' });
  });

  it('summarizes the data first, then shows a change to it with .undo()', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    fireEvent.change(await screen.findByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52 %\n2.0,58 %\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(thread.firstElementChild).toHaveTextContent('.summarize_data()');
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or for a fix: "sum per month"'
    );

    // A correction in words, before the confirmation: the card shows it in place.
    const send = screen.getByRole('button', { name: '.send()' });
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'das ist prozent' } });
    await waitFor(() => expect(send).toBeEnabled());
    fireEvent.click(send);
    const change = await screen.findByTestId('data-change');
    await turnEnded();
    expect(within(change).getByText('# changed · version 2')).toBeInTheDocument();
    expect(within(change).getByText(PREPARED.changes[0])).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
    expect(screen.getByText('1 data')).toHaveAttribute('aria-current', 'step');
    expect(quietCreate()).toBeEnabled();
    // Nothing was confirmed yet, so nothing was lost.
    expect(screen.queryByTestId('confirm-lost')).not.toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    const confirm = screen.getByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    expect(await screen.findByTestId('data-summary')).toHaveTextContent('version 2');
    expect(screen.queryByTestId('data-change')).not.toBeInTheDocument();

    // The change and its `.undo()` are one `.show()` away; an undo is step 1 again.
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    const undo = within(screen.getByTestId('data-change')).getByRole('button', { name: '.undo()' });
    expect(undo).toBeEnabled();
    fireEvent.click(undo);
    expect(await screen.findByText('# undone · back to version 1')).toBeInTheDocument();
    expect(screen.getByTestId('data-summary')).toHaveTextContent('confirm again');
    expect(lastInThread()).toHaveTextContent('# the data changed · confirm it again');
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(screen.getByText('1 data')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();
    expect(screen.getByRole('cell', { name: '52' })).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_undo', { version: '1' });
    // An undo asks for no new summary.
    expect(turnBodies()).toHaveLength(2);
  });

  it('sends a pasted formula to the chat, whose table becomes version 1', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    const textbox = await screen.findByLabelText(/# your data/);
    // Without data, both boxes name the other sources: example data, and a curve the assistant computes.
    expect(textbox).toHaveAccessibleDescription(
      'or type example data here, or ask for a curve in the chat: y = sin(x), x from -pi to pi'
    );
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask for example data or a curve: "y = sin(x), x from -pi to pi"'
    );
    expect(screen.getByText(/or ask here for example data or a curve/)).toBeInTheDocument();

    fireEvent.change(textbox, { target: { value: FORMULA } });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    // The data panel's own .send(), next to the line; the composer has one too.
    const offer = await screen.findByTestId('formula-offer');
    const send = within(offer).getByRole('button', { name: '.send()' });
    expect(send).toHaveAccessibleDescription(/looks like a formula/);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    fireEvent.click(send);
    expect(await screen.findByText('I generated 200 rows from y = sin(x).')).toBeInTheDocument();
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(within(thread).getByText(FORMULA)).toBeInTheDocument();
    expect(textbox).toHaveValue('');
    expect(screen.queryByTestId('formula-offer')).not.toBeInTheDocument();

    const change = await screen.findByTestId('data-change');
    expect(within(change).getByText('# changed · version 1')).toBeInTheDocument();
    expect(within(change).getByText(GENERATED.changes[0])).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toHaveValue('x');
    expect(screen.getByRole('cell', { name: '-1.2246468e-16' })).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    const confirm = screen.getByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    await screen.findByTestId('data-pinned');
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
  });

  it('collapses the confirmed data into a pinned header that .show() opens and .hide() closes', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/# your data/)).not.toBeInTheDocument();
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
    expect(card.queryByRole('button', { name: '.confirm()' })).not.toBeInTheDocument();
    expect(currentStep()).toEqual(['·2 plot']);
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();

    fireEvent.click(hide);
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Show the data' })).toBeInTheDocument();
  });

  it('goes back to step 1 with the card open when a binding changes in step 2', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });

    const confirm = await screen.findByRole('button', { name: '.confirm()' });
    // The header stays, now in step 1's words, and leads back to the open card.
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'confirm again · 2 rows · 2 columns · version 1'
    );
    expect(screen.getByRole('button', { name: 'Go to the data' })).toBeInTheDocument();
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(currentStep()).toEqual(['1 data']);
    expect(quietCreate()).toBeEnabled();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or for a fix: "sum per month"'
    );
    // The loss is named where it happened, right after the change, and next to `.confirm()`.
    expect(lastInThread()).toHaveTextContent('# bindings changed · confirm the data again');
    expect(screen.getByTestId('confirm-lost')).toBe(lastInThread());
    expect(confirm).toHaveAccessibleDescription(
      '# step 1 again — bindings changed · confirm the data again'
    );

    // Back and forth: the confirmation is gone already, so one notice says it.
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'score' } });
    await waitFor(() => expect(screen.getByLabelText(/^y/)).toBeEnabled());
    expect(screen.getAllByTestId('confirm-lost')).toHaveLength(1);

    // Confirmed again, the card collapses again, and the row's reason goes with the step.
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    expect(await screen.findByTestId('data-pinned')).toBeInTheDocument();
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(screen.getByTestId('data-summary')).toHaveTextContent('data fits');
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.queryByTestId('data-step')).not.toBeInTheDocument();
  });

  it('names the loss for the data the card shows after it, never for a new paste', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    fireEvent.change(screen.getByLabelText(/^y/), { target: { value: 'hours' } });
    await waitFor(() => expect(screen.getByLabelText(/^y/)).toBeEnabled());
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      '# step 1 again — bindings changed · confirm the data again'
    );

    // A data request after the loss: the step line names the change the preview shows.
    sendFromComposer('read score as prozent');
    expect(await screen.findByText('I read score as numbers.')).toBeInTheDocument();
    await turnEnded();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      '# step 1 again — the data changed · confirm it again'
    );

    // A new paste is data nobody confirmed: plain step 1, and the thread keeps one notice.
    fireEvent.change(screen.getByLabelText(/# your data/), {
      target: { value: 'hours,score\n3,70\n4,80\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    await waitFor(() => expect(screen.getAllByText(SUMMARY)).toHaveLength(2));
    await turnEnded();
    expect(screen.getByTestId('data-step')).toHaveTextContent(
      '# step 1 — check the preview and the bindings, then confirm'
    );
    expect(screen.getAllByTestId('confirm-lost')).toHaveLength(1);
  });

  it('starts the first plot from an empty box with .create_plot(), never on Enter', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    const box = screen.getByLabelText('Message');
    expect(box).toHaveAttribute(
      'placeholder',
      'optional: what the first plot should do differently'
    );
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(turnBodies()).toEqual([{ action: 'summarize_data' }]);

    // A pointer click moves no focus into the box, so a phone opens no keyboard.
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }), { detail: 1 });
    expect(box).not.toHaveFocus();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    expect(lastTurn()).toEqual({ action: 'create_plot' });
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(within(thread).getByText('.create_plot()')).toBeInTheDocument();
  });

  it('sends a note typed before the first plot as the turn that makes it, then refines', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    expect(lastTurn()).toEqual({ text: 'log scale on y' });
    const thread = screen.getByRole('log', { name: 'Conversation' });
    expect(within(thread).getByText('log scale on y')).toBeInTheDocument();
    expect(within(thread).queryByText('.create_plot()')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveValue('');

    // This library has a plot: the composer refines, and starting over is one quiet click
    // that says what it does, unlike `.send()` beside it.
    expect(screen.getByRole('article', { name: 'Plot version 1' })).toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about this plot, or ask for a change'
    );
    expect(screen.getByRole('button', { name: '.send()' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver).toBeEnabled();
    expect(startOver).toHaveTextContent('.start_over()');
    expect(startOver).toHaveAccessibleDescription(
      expect.stringContaining('new from the catalogue plot, without your changes')
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
      await parseAndConfirm();
      fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
      expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
      await turnEnded();
      expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();

      // A change to the data asked for below the plot, with the card collapsed.
      sendFromComposer('das ist prozent');
      const change = await screen.findByTestId('data-change');
      await turnEnded();
      expect(within(change).getByText('# changed · version 2')).toBeInTheDocument();
      expect(within(change).getByRole('button', { name: '.undo()' })).toBeEnabled();
      expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
      expect(currentStep()).toEqual(['1 data']);
      expect(quietCreate('Start over')).toBeEnabled();
      expect(lastInThread()).toHaveTextContent('# the data changed · confirm it again');
      // The header stays pinned in view and leads to the card's top, far above.
      expect(screen.getByTestId('data-summary')).toHaveTextContent(
        'confirm again · 2 rows · 2 columns · version 2'
      );
      scroll.mockClear();
      fireEvent.click(screen.getByRole('button', { name: 'Go to the data' }));
      expect(scroll.mock.contexts).toEqual([screen.getByTestId('data-card')]);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });

      // Confirmed again with a plot already there: the keyboard lands on the header's
      // toggle, not on a fresh run.
      const confirm = screen.getByRole('button', { name: '.confirm()' });
      await waitFor(() => expect(confirm).toBeEnabled());
      confirm.focus();
      fireEvent.click(confirm);
      const show = await screen.findByRole('button', { name: 'Show the data' });
      await waitFor(() => expect(show).toHaveFocus());
      expect(screen.getByRole('button', { name: 'Start over' })).not.toHaveFocus();
    } finally {
      delete (Element.prototype as Partial<Element>).scrollIntoView;
    }
  });

  it('holds step 1 while a table read from text waits, whatever a turn reports', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    await transcribeInStep2();
    expect(currentStep()).toEqual(['1 data']);

    // The server keeps its confirmation of the stored data, and the turn's sync says so;
    // the text still goes as a turn.
    sendFromComposer('what columns are there?');
    expect(await screen.findByText('Two columns: hours and score.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ text: 'what columns are there?' });
    expect(currentStep()).toEqual(['1 data']);
    expect(screen.getByTestId('transcription-card')).toBeInTheDocument();
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'decide on the table first: .use() or .discard()'
    );
    expect(quietCreate()).toBeEnabled();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or for a fix: "sum per month"'
    );

    // Discarded, the stored data is the confirmed data again.
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(currentStep()).toEqual(['·2 plot']);
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
  });

  it('returns to step 2 when a table read from text is discarded at once', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    await transcribeInStep2();
    expect(currentStep()).toEqual(['1 data']);

    // The transcription stored nothing and the server kept its confirmation: discarding it
    // is back where the user was, with no turn in between.
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(currentStep()).toEqual(['·2 plot']);
    expect(screen.getByTestId('data-summary')).toHaveTextContent('data fits');
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
    expect(screen.queryByTestId('transcription-card')).not.toBeInTheDocument();
  });

  it("leaves the composer's focus alone when step 2 returns without the user's .confirm()", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    await transcribeInStep2();
    expect(currentStep()).toEqual(['1 data']);

    const box = screen.getByLabelText('Message');
    box.focus();
    // A turn's sync confirms the data again while the table still waits: step 1 holds.
    sendFromComposer('what columns are there?');
    expect(await screen.findByText('Two columns: hours and score.')).toBeInTheDocument();
    await turnEnded();
    expect(currentStep()).toEqual(['1 data']);
    expect(box).toHaveFocus();

    // Discarding the table brings step 2 back with no `.confirm()` of the user's: the next
    // key press still types into the box.
    fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(currentStep()).toEqual(['·2 plot']);
    expect(box).toHaveFocus();
    expect(screen.getByRole('button', { name: 'Create plot' })).not.toHaveFocus();
  });

  it('never spends a second key press on stopping the run it started', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    const create = screen.getByRole('button', { name: 'Create plot' });
    await waitFor(() => expect(create).toHaveFocus());

    // Enter on the focused button: a click with `detail` 0. The focus continues in the
    // box, and `.stop()` is a button of its own, not the one that had the focus.
    fireEvent.click(create, { detail: 0 });
    const box = screen.getByLabelText('Message');
    expect(box).toHaveFocus();
    const stop = screen.getByRole('button', { name: 'Stop' });
    expect(stop).not.toBe(create);
    expect(stop).not.toHaveFocus();
    fireEvent.keyDown(box, { key: 'Enter' });

    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
    await turnEnded();
    expect(turnBodies()).toEqual([{ action: 'summarize_data' }, { action: 'create_plot' }]);
    expect(agentCalls().some(([input]) => String(input).endsWith('/cancel'))).toBe(false);
    expect(box).toHaveFocus();
  });

  it("holds back the composer's .create_plot() while a parse runs", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    const create = screen.getByRole('button', { name: 'Create plot' });
    expect(create).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    fireEvent.change(screen.getByLabelText(/# your data/), {
      target: { value: 'slow,data\n1,2\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    await waitFor(() => expect(releaseParse).not.toBeNull());
    expect(create).toBeDisabled();

    // A new parse is new data: step 1 again.
    releaseParse?.();
    expect(await screen.findByRole('button', { name: '.confirm()' })).toBeInTheDocument();
    expect(currentStep()).toEqual(['1 data']);
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
    expect(screen.getByRole('button', { name: 'reload to sign in again' })).toBeInTheDocument();
    sessionStorage.clear();
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
    await screen.findByLabelText(/# your data/);
    expect(unload()).toBe(false);

    fireEvent.click(await screen.findByRole('link', { name: /Basic Scatter Plot/ }));
    await waitFor(() => expect(screen.queryByLabelText(/# your data/)).not.toBeInTheDocument());
    expect(screen.getByTestId('location')).toHaveTextContent('/scatter-basic');
    expect(confirm).not.toHaveBeenCalled();
  });

  it('asks before a reload or a link drops the data, and lets its own query edits pass', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    expect(unload()).toBe(true);

    // The `all` pill writes the query on the same path: nothing to ask.
    const all = await screen.findByRole('button', { name: 'All libraries' });
    await waitFor(() => expect(all).toBeEnabled());
    fireEvent.click(all);
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
  it('says that the data is being parsed, under .parse() and to a screen reader', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    fireEvent.change(await screen.findByLabelText(/# your data/), {
      target: { value: 'slow,data\n1,2\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    await waitFor(() => expect(releaseParse).not.toBeNull());

    expect(screen.getByTestId('parse-hint')).toHaveTextContent('# parsing your data …');
    const parse = screen.getByRole('button', { name: '.parse() …' });
    expect(parse).toBeDisabled();
    expect(parse).toHaveAccessibleDescription('# parsing your data');
    expect(screen.getByTestId('data-step-status')).toHaveTextContent('parsing your data');

    releaseParse?.();
    await waitFor(() =>
      expect(screen.getByTestId('data-step-status')).toHaveTextContent(
        'step 1: check the data, then confirm it'
      )
    );
    expect(screen.queryByTestId('parse-hint')).not.toBeInTheDocument();
  });

  it('holds the summary turn in the thread and says why the bindings wait', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    fireEvent.change(await screen.findByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));

    const pending = await screen.findByTestId('pending-reply');
    expect(pending).toHaveTextContent('summarizing your data …');
    expect(lastInThread()).toBe(pending);
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      '# bindings and .confirm() wait while the assistant works …'
    );
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();
    // One indicator: a turn without pipeline steps mounts no progress timeline.
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Stop' })).toBeInTheDocument();

    releaseTurn?.();
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
  });

  it('puts an in-progress line in the thread for a question, and leaves a plot run to the timeline', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();

    holdNextTurn = true;
    sendFromComposer('what is the mean score?');
    const pending = await screen.findByTestId('pending-reply');
    expect(pending).toHaveTextContent('working on your message …');
    expect(screen.queryByRole('table', { name: 'Progress' })).not.toBeInTheDocument();
    releaseTurn?.();
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
    await turnEnded();

    // `.create_plot()` shows its path in the timeline from the start; the thread adds nothing.
    holdNextTurn = true;
    fireEvent.click(screen.getByRole('button', { name: 'Create plot' }));
    expect(await screen.findByRole('table', { name: 'Progress' })).toBeInTheDocument();
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
    releaseTurn?.();
    expect(await screen.findByText('Here is your plot.')).toBeInTheDocument();
  });

  it('keeps .create_plot() in the composer before the confirmation and leads to .confirm()', async () => {
    const scroll = stubScrollIntoView();
    try {
      localStorage.setItem(ADMIN_HINT_KEY, '1');
      renderAt(PAGE);
      fireEvent.change(await screen.findByLabelText(/# your data/), {
        target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
      });
      fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
      expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
      await turnEnded();
      const box = screen.getByLabelText('Message');
      box.focus();

      const create = quietCreate();
      expect(create).toBeEnabled();
      expect(screen.getByRole('button', { name: '.send()' })).toBeInTheDocument();
      expect(screen.getByTestId('composer-status')).toBeEmptyDOMElement();
      scroll.mockClear();
      fireEvent.click(create);

      const notice = screen.getByTestId('create-gate');
      // It opens under the composer, which can sit at the window's edge: it is brought in.
      expect(scroll.mock.contexts).toEqual([notice]);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'nearest' });
      const text = 'confirm the data first · .confirm() sits at the foot of the data card';
      expect(notice).toHaveTextContent(`# ${text}`);
      expect(screen.getByTestId('composer-status')).toHaveTextContent(text);
      expect(create).toHaveAccessibleDescription(`# ${text}`);
      // No call: the server would answer data_unconfirmed. No focus taken either.
      expect(turnBodies()).toEqual([{ action: 'summarize_data' }]);
      expect(box).toHaveFocus();

      scroll.mockClear();
      fireEvent.click(within(notice).getByRole('button', { name: 'Go to the confirmation' }));
      const confirm = screen.getByRole('button', { name: '.confirm()' });
      expect(scroll.mock.contexts).toEqual([confirm]);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
      expect(confirm).toHaveFocus();

      fireEvent.click(confirm);
      await screen.findByTestId('data-pinned');
      expect(screen.queryByTestId('create-gate')).not.toBeInTheDocument();
      expect(screen.getByTestId('composer-status')).toBeEmptyDOMElement();
      expect(screen.getByRole('button', { name: 'Create plot' })).toHaveAttribute('type', 'submit');
    } finally {
      restoreScrollIntoView();
    }
  });

  it('clears the notice before the confirmation when a turn starts', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    fireEvent.change(await screen.findByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    fireEvent.click(quietCreate());
    expect(screen.getByTestId('create-gate')).toBeInTheDocument();

    sendFromComposer('what is the mean score?');
    expect(screen.queryByTestId('create-gate')).not.toBeInTheDocument();
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    expect(currentStep()).toEqual(['1 data']);
    expect(screen.queryByTestId('create-gate')).not.toBeInTheDocument();
  });

  it('leads to .use() while a table read from text waits', async () => {
    const scroll = stubScrollIntoView();
    try {
      localStorage.setItem(ADMIN_HINT_KEY, '1');
      renderAt(PAGE);
      await parseAndConfirm();
      await transcribeInStep2();

      fireEvent.click(quietCreate());
      const notice = screen.getByTestId('create-gate');
      expect(notice).toHaveTextContent(
        '# decide on the table first · .use() or .discard() sit in the data card'
      );
      fireEvent.click(within(notice).getByRole('button', { name: 'Go to the table' }));
      const use = screen.getByRole('button', { name: '.use()' });
      expect(scroll.mock.contexts).toContain(use);
      expect(use).toHaveFocus();
      expect(turnBodies()).toEqual([{ action: 'summarize_data' }]);
    } finally {
      restoreScrollIntoView();
    }
  });

  it('names what the data card asks for now when a table read from text comes or goes', async () => {
    const scroll = stubScrollIntoView();
    try {
      localStorage.setItem(ADMIN_HINT_KEY, '1');
      renderAt(PAGE);
      fireEvent.change(await screen.findByLabelText(/# your data/), {
        target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
      });
      fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
      expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
      await turnEnded();
      const confirmText = 'confirm the data first · .confirm() sits at the foot of the data card';
      const tableText = 'decide on the table first · .use() or .discard() sit in the data card';
      fireEvent.click(quietCreate());
      expect(screen.getByTestId('create-gate')).toHaveTextContent(`# ${confirmText}`);

      // Free text pasted in step 1 comes back as a table to decide on, and no turn starts:
      // the notice now leads to `.use()`, since `.confirm()` waits for that decision.
      scroll.mockClear();
      fireEvent.change(screen.getByLabelText(/# your data/), { target: { value: FREE_TEXT } });
      fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
      await screen.findByTestId('transcription-card');
      const notice = screen.getByTestId('create-gate');
      expect(notice).toHaveTextContent(`# ${tableText}`);
      expect(screen.getByTestId('composer-status')).toHaveTextContent(tableText);
      // The user works in the data card: a change of the wording leaves the window there.
      expect(scroll.mock.contexts).not.toContain(notice);
      fireEvent.click(within(notice).getByRole('button', { name: 'Go to the table' }));
      const use = screen.getByRole('button', { name: '.use()' });
      expect(scroll.mock.contexts).toContain(use);
      expect(use).toHaveFocus();

      // Discarded, the card asks for `.confirm()` again, and so does the notice's `.show()`.
      fireEvent.click(screen.getByRole('button', { name: '.discard()' }));
      expect(screen.getByTestId('create-gate')).toHaveTextContent(`# ${confirmText}`);
      expect(screen.getByTestId('composer-status')).toHaveTextContent(confirmText);
      scroll.mockClear();
      fireEvent.click(
        within(screen.getByTestId('create-gate')).getByRole('button', {
          name: 'Go to the confirmation',
        })
      );
      const confirm = screen.getByRole('button', { name: '.confirm()' });
      expect(scroll.mock.contexts).toEqual([confirm]);
      expect(confirm).toHaveFocus();
      expect(turnBodies()).toEqual([{ action: 'summarize_data' }]);
    } finally {
      restoreScrollIntoView();
    }
  });
});

describe('AgentChatPage .plot_all()', () => {
  /** The fetch stub as `stubFetch` set it, for a test that answers one route differently. */
  const baseFetch = () =>
    fetchMock.getMockImplementation() as (input: string, init?: RequestInit) => Promise<Response>;
  const libraryGroup = () => screen.getByRole('group', { name: 'Library' });
  const libraryPill = (name: string) => within(libraryGroup()).getByRole('button', { name });
  const plotAllButton = () => screen.getByRole('button', { name: 'Plot in all libraries' });

  it('offers all once the lists are in, and plots the confirmed table in every library', async () => {
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
    await parseAndConfirm();
    expect(screen.queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    releaseStatus();

    const all = await screen.findByRole('button', { name: 'All libraries' });
    expect(all).toHaveTextContent('all');
    expect(all.parentElement).toBe(libraryGroup());
    expect(all).toHaveAttribute('aria-pressed', 'false');
    expect(libraryPill('matplotlib')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.queryByRole('button', { name: 'Plot in all libraries' })).not.toBeInTheDocument();

    // Pressed, `all` is the pressed pill, and the composer's create action plots everywhere.
    fireEvent.click(all);
    expect(all).toHaveAttribute('aria-pressed', 'true');
    expect(libraryPill('matplotlib')).toHaveAttribute('aria-pressed', 'false');
    expect(libraryPill('matplotlib')).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    const plotAll = plotAllButton();
    expect(plotAll).toHaveTextContent('.plot_all()');
    expect(plotAll).toBeEnabled();
    const line =
      '# step 2 — plot the table as it is in all 2 libraries at once · turn all off to chat';
    expect(plotAll).toHaveAccessibleDescription(expect.stringContaining(line));
    expect(screen.queryByTestId('plot-all-hint')).not.toBeInTheDocument();
    // The fan-out takes no text: in step 2 the message box waits, and the line says why.
    const box = screen.getByLabelText('Message');
    expect(box).toBeDisabled();
    expect(box).toHaveAccessibleDescription(line);
    expect(box).toHaveAttribute(
      'placeholder',
      'all libraries: the table goes as it is · turn all off to chat'
    );

    fireEvent.click(plotAll, { detail: 1 });
    const panel = await screen.findByRole('region', { name: 'All libraries' });
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
    expect(all).toBeDisabled();
    expect(all).toHaveAttribute('aria-pressed', 'true');
    expect(libraryPill('matplotlib')).toBeDisabled();
    expect(libraryPill('seaborn')).toBeDisabled();

    // `.close()` goes with the panel: the focus returns to `.plot_all()`, which opened it.
    const close = within(panel).getByRole('button', { name: 'Close all libraries' });
    close.focus();
    fireEvent.click(close);
    expect(screen.queryByRole('region', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(plotAllButton()).toBeEnabled();
    expect(plotAllButton()).toHaveFocus();
    expect(all).toBeEnabled();
    expect(libraryPill('matplotlib')).toBeEnabled();
    expect(libraryPill('seaborn')).toBeEnabled();

    // A key press (a click with `detail` 0) continues in the panel it opened.
    fireEvent.click(plotAllButton(), { detail: 0 });
    expect(await screen.findByRole('region', { name: 'All libraries' })).toHaveFocus();
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
    await parseAndConfirm();
    await waitFor(() =>
      expect(within(libraryGroup()).queryByRole('button', { name: 'seaborn' })).toBeNull()
    );
    expect(screen.queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create plot' })).toBeEnabled();
  });

  it('turns all off from any library pill: the own one only that, another switches', async () => {
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
    await parseAndConfirm();
    const all = await screen.findByRole('button', { name: 'All libraries' });
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'log scale on y' } });

    // `all` itself is a toggle: a second click turns it off again.
    fireEvent.click(all);
    expect(screen.getByLabelText('Message')).toBeDisabled();
    fireEvent.click(all);
    expect(all).toHaveAttribute('aria-pressed', 'false');
    expect(libraryPill('matplotlib')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveTextContent('.create_plot()');
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).not.toHaveAccessibleDescription();

    fireEvent.click(all);
    fireEvent.click(libraryPill('matplotlib'));
    expect(all).toHaveAttribute('aria-pressed', 'false');
    // The pill pressed now is disabled: the keyboard continues at `all`.
    expect(all).toHaveFocus();
    expect(libraryPill('matplotlib')).toHaveAttribute('aria-pressed', 'true');
    expect(libraryPill('matplotlib')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveTextContent('.create_plot()');
    // The draft waited in the box, and nothing switched.
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).toHaveValue('log scale on y');
    expect(agentCalls().filter(([input]) => String(input).endsWith('/library'))).toEqual([]);

    fireEvent.click(all);
    fireEvent.click(libraryPill('seaborn'));
    expect(all).toHaveAttribute('aria-pressed', 'false');
    await waitFor(() =>
      expect(screen.getByTestId('location')).toHaveTextContent('library=seaborn')
    );
    expect(libraryPill('seaborn')).toHaveAttribute('aria-pressed', 'true');
    expect(libraryPill('matplotlib')).toHaveAttribute('aria-pressed', 'false');
  });

  it('leaves the chat about the data usable with all pressed, before data and in step 1', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    const all = await screen.findByRole('button', { name: 'All libraries' });
    await waitFor(() => expect(all).toBeEnabled());

    // Without data: nothing to plot yet, and the box asks for a curve as without `all`.
    fireEvent.click(all);
    expect(all).toHaveAttribute('aria-pressed', 'true');
    expect(screen.queryByRole('button', { name: 'Plot in all libraries' })).not.toBeInTheDocument();
    const box = screen.getByLabelText('Message');
    expect(box).toBeEnabled();
    expect(box).toHaveAttribute(
      'placeholder',
      'ask for example data or a curve: "y = sin(x), x from -pi to pi"'
    );
    expect(box).not.toHaveAccessibleDescription();

    // Step 1: `.plot_all()` waits for the confirmation, and a question about the data goes.
    fireEvent.change(screen.getByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();
    expect(currentStep()).toEqual(['1 data']);
    expect(plotAllButton()).toBeEnabled();
    expect(screen.getByLabelText('Message')).toBeEnabled();
    expect(screen.getByLabelText('Message')).toHaveAttribute(
      'placeholder',
      'ask about your data, or for a fix: "sum per month"'
    );
    sendFromComposer('what is the mean score?');
    expect(await screen.findByText('The mean score is 55.')).toBeInTheDocument();
    await turnEnded();
    expect(lastTurn()).toEqual({ text: 'what is the mean score?' });
    expect(all).toHaveAttribute('aria-pressed', 'true');

    // Confirmed, step 2 is where `.plot_all()` is the action: the box waits from here.
    const confirm = screen.getByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    await waitFor(() => expect(currentStep()).toEqual(['·2 plot']));
    expect(screen.getByLabelText('Message')).toBeDisabled();
    expect(plotAllButton()).toBeEnabled();
  });

  it('leads to .confirm() first, like .create_plot()', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    fireEvent.change(await screen.findByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(await screen.findByText(SUMMARY)).toBeInTheDocument();
    await turnEnded();

    fireEvent.click(await screen.findByRole('button', { name: 'All libraries' }));
    const plotAll = plotAllButton();
    expect(plotAll).toHaveAttribute('type', 'button');
    expect(plotAll).toBeEnabled();
    fireEvent.click(plotAll);
    const text = 'confirm the data first · .confirm() sits at the foot of the data card';
    expect(screen.getByTestId('create-gate')).toHaveTextContent(`# ${text}`);
    expect(plotAll).toHaveAccessibleDescription(`# ${text}`);
    expect(screen.queryByRole('region', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(turnBodies()).toEqual([{ action: 'summarize_data' }]);
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
    await screen.findByLabelText(/# your data/);
    sendFromComposer('y = sin(x), x from -pi to pi');
    expect(await screen.findByText('I generated 200 rows from y = sin(x).')).toBeInTheDocument();
    await turnEnded();
    const confirm = screen.getByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    await waitFor(() => expect(currentStep()).toEqual(['·2 plot']));

    fireEvent.click(await screen.findByRole('button', { name: 'All libraries' }));
    // Computed data has no paste, and `.plot_all()` needs none: it is the action, with no hint.
    const plotAll = plotAllButton();
    expect(plotAll).toBeEnabled();
    expect(screen.queryByTestId('plot-all-hint')).not.toBeInTheDocument();
    fireEvent.click(plotAll, { detail: 1 });

    const panel = await screen.findByRole('region', { name: 'All libraries' });
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
    await parseAndConfirm();
    fireEvent.click(await screen.findByRole('button', { name: 'All libraries' }));
    fireEvent.click(plotAllButton(), { detail: 1 });
    const panel = await screen.findByRole('region', { name: 'All libraries' });

    // Opening the card is only a look: it opens, but nothing in it changes the data.
    fireEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    const card = screen.getByRole('region', { name: 'Your data' });
    const line = '# the data waits while all libraries plot it · .close() the panel to change it';
    expect(within(card).getByTestId('data-lock')).toHaveTextContent(line);
    expect(card).toHaveAccessibleDescription(line);
    expect(within(card).getByRole('button', { name: 'Open a data file' })).toBeDisabled();
    expect(within(card).getByLabelText(/^x/)).toBeDisabled();
    fireEvent.change(within(card).getByLabelText(/# your data/), {
      target: { value: 'hours,score\n9,99\n8,88\n' },
    });
    expect(within(card).getByRole('button', { name: '.parse()' })).toBeDisabled();

    fireEvent.click(within(panel).getByRole('button', { name: 'Close all libraries' }));
    expect(screen.queryByTestId('data-lock')).not.toBeInTheDocument();
    const reopened = screen.getByRole('region', { name: 'Your data' });
    expect(reopened).not.toHaveAccessibleDescription();
    expect(within(reopened).getByRole('button', { name: '.parse()' })).toBeEnabled();
    expect(within(reopened).getByLabelText(/^x/)).toBeEnabled();
  });

  it('posts the paste again in every library while the server has no copy', async () => {
    fanOutSessions(() => json(404, { detail: 'not_found', ref: 'r-404' }));
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    await parseAndConfirm();
    fireEvent.click(await screen.findByRole('button', { name: 'All libraries' }));
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
  const libraryGroup = () => screen.getByRole('group', { name: 'Library' });
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
    // The header moves into the chat column once the session is open: look for the pills there.
    await screen.findByLabelText(/# your data/);
    const ggplot2 = await within(libraryGroup()).findByRole('button', { name: 'ggplot2' });
    await waitFor(() => expect(ggplot2).toBeEnabled());

    fireEvent.click(ggplot2);
    await waitFor(() => expect(query().get('library')).toBe('ggplot2'));
    expect(query().get('language')).toBe('r');
    expect(within(libraryGroup()).getByText('r ·')).toBeInTheDocument();

    const seaborn = within(libraryGroup()).getByRole('button', { name: 'seaborn' });
    await waitFor(() => expect(seaborn).toBeEnabled());
    fireEvent.click(seaborn);
    await waitFor(() => expect(query().get('library')).toBe('seaborn'));
    expect(query().get('language')).toBe('python');
    expect(query().get('spec')).toBe('scatter-basic');
  });

  it('keeps the all pill in the URL, and presses it again from there once the lists are in', async () => {
    let releaseStatus!: () => void;
    threeLibraries(new Promise<void>(resolve => (releaseStatus = resolve)));
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const first = renderAt(PAGE);
    releaseStatus();
    const all = await screen.findByRole('button', { name: 'All libraries' });
    await waitFor(() => expect(all).toBeEnabled());
    expect(query().has('all')).toBe(false);

    fireEvent.click(all);
    await waitFor(() => expect(query().get('all')).toBe('1'));
    fireEvent.click(all);
    await waitFor(() => expect(query().has('all')).toBe(false));
    fireEvent.click(all);
    await waitFor(() => expect(query().get('all')).toBe('1'));
    const reloaded = location();
    first.unmount();

    // The reload: until the lists are in, `all` is not offered, and the URL keeps it.
    threeLibraries(new Promise<void>(resolve => (releaseStatus = resolve)));
    renderAt(reloaded);
    await screen.findByLabelText(/# your data/);
    expect(screen.queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(query().get('all')).toBe('1');
    releaseStatus();
    const again = await screen.findByRole('button', { name: 'All libraries' });
    expect(again).toHaveAttribute('aria-pressed', 'true');
    expect(within(libraryGroup()).getByRole('button', { name: 'matplotlib' })).toHaveAttribute(
      'aria-pressed',
      'false'
    );
    expect(query().get('all')).toBe('1');
  });

  it('drops all from the URL with the pill: a library pill, and a page that offers none', async () => {
    threeLibraries();
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const first = renderAt(`${PAGE}&all=1`);
    const all = await screen.findByRole('button', { name: 'All libraries' });
    await waitFor(() => expect(all).toBeEnabled());
    expect(all).toHaveAttribute('aria-pressed', 'true');

    // Another library switches and turns `all` off: the URL names the new library, without `all`.
    fireEvent.click(within(libraryGroup()).getByRole('button', { name: 'seaborn' }));
    await waitFor(() => expect(query().get('library')).toBe('seaborn'));
    expect(query().has('all')).toBe(false);
    expect(all).toHaveAttribute('aria-pressed', 'false');
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
    expect(screen.queryByRole('button', { name: 'All libraries' })).not.toBeInTheDocument();
    expect(query().get('library')).toBe('matplotlib');
  });
});
