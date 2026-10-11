import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AgentChatPage } from 'src/pages/AgentChatPage';
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

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Stable identities, like the real hook (effects depend on them).
const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

let fetchMock: ReturnType<typeof vi.fn>;

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

const SUMMARY = '2 rows: hours and score, both numbers. Is hours the x axis?';

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
      return sse(turnEvents(JSON.parse(String(init.body))));
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

function renderAt(url: string) {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route
            path="/debug/agent"
            element={
              <>
                <AgentChatPage />
                <LocationProbe />
              </>
            }
          />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>
  );
}

const PAGE = '/debug/agent?spec=scatter-basic&library=matplotlib&language=python';
const agentCalls = () =>
  fetchMock.mock.calls.filter(([input]) => String(input).includes('/debug/agent'));

beforeEach(() => {
  flags.agentChat = true;
  flags.isDev = false;
  localStorage.clear();
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
    const current = () =>
      within(screen.getByRole('list', { name: 'Steps' }))
        .getAllByRole('listitem')
        .filter(item => item.getAttribute('aria-current') === 'step')
        .map(item => item.textContent);
    expect(await screen.findByLabelText(/# your data/)).toBeInTheDocument();
    expect(current()).toEqual(['1 data']);
    expect(
      screen.getByText(/check the preview and the bindings, confirm, then/)
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    const confirm = await screen.findByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();

    fireEvent.click(confirm);
    expect(await screen.findByRole('button', { name: '.create_plot()' })).toBeEnabled();
    expect(current()).toEqual(['·2 plot']);
    expect(screen.getByTestId('data-step')).toHaveTextContent('data fits · 2 rows · 2 columns');
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_confirmed', {
      size_bucket: 'lt_1kb',
    });
    // The chat composer was usable the whole time; it is not part of the steps.
    expect(screen.getByLabelText('Message')).toBeEnabled();
  });

  it("goes back to step 1 with the dropdowns the turn's done reports", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    fireEvent.change(await screen.findByLabelText(/# your data/), {
      target: { value: 'hours,score\n1.5,52\n2.0,58\n' },
    });
    fireEvent.click(screen.getByRole('button', { name: '.parse()' }));
    const confirm = await screen.findByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    expect(await screen.findByRole('button', { name: '.create_plot()' })).toBeEnabled();
    expect(screen.getByLabelText(/^x/)).toHaveValue('hours');

    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'swap x and y' } });
    fireEvent.click(screen.getByRole('button', { name: '.send()' }));
    expect(await screen.findByText('Swapped.')).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: '.confirm()' })).toBeEnabled();
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toHaveValue('score');
    expect(screen.getByLabelText(/^y/)).toHaveValue('hours');
    expect(screen.getByText('1 data')).toHaveAttribute('aria-current', 'step');
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
    const confirm = screen.getByRole('button', { name: '.confirm()' });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    expect(await screen.findByRole('button', { name: '.create_plot()' })).toBeEnabled();

    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'das ist prozent' } });
    fireEvent.click(screen.getByRole('button', { name: '.send()' }));
    const change = await screen.findByTestId('data-change');
    expect(within(change).getByText('# changed · version 2')).toBeInTheDocument();
    expect(within(change).getByText(PREPARED.changes[0])).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '0.52' })).toBeInTheDocument();
    expect(screen.getByText('1 data')).toHaveAttribute('aria-current', 'step');
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_prepared', { changes: '1' });

    const undo = screen.getByRole('button', { name: '.undo()' });
    await waitFor(() => expect(undo).toBeEnabled());
    fireEvent.click(undo);
    expect(await screen.findByText('# undone · back to version 1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();
    expect(screen.getByRole('cell', { name: '52' })).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_data_undo', { version: '1' });
    // An undo asks for no new summary.
    const turns = agentCalls().filter(([input]) => String(input).endsWith('/messages'));
    expect(turns).toHaveLength(2);
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
