/**
 * Quick feedback on the chat page: the result card's control stores the
 * version's case through the BFF, shows `sent · v<n>`, takes an edit, and shows
 * a failure line. The flows of the page are in AgentChatPage.test.tsx; this
 * file stubs only the calls a plot and its feedback need.
 */

import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
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

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

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

const PLOT = {
  status: 'ok',
  attempts: 1,
  artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
  changes: [],
  residual_defects: [],
  version: 1,
};

const PAGE = '/debug/agent?spec=scatter-basic&library=matplotlib&language=python';

let feedbackBodies: unknown[];
let feedbackAnswer: () => Response;
/** A turn that answers in words only: the session keeps no plot. */
let wordsOnly: boolean;
/** Set to hold the next turn's answer until the test resolves it. */
let hold: Promise<void> | null;

function stubFetch() {
  feedbackBodies = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      if (url.pathname.endsWith('/debug/agent/sessions') && method === 'POST') {
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      if (url.pathname.endsWith('/sessions/S1/messages') && method === 'POST') {
        if (hold) await hold;
        if (wordsOnly) {
          return sse([
            ['message', { text: 'The feature role needs names, not numbers.' }],
            ['done', { llm_calls: 1 }],
          ]);
        }
        return sse([
          ['plot', PLOT],
          ['message', { text: 'Here is your plot.' }],
          ['done', { llm_calls: 2 }],
        ]);
      }
      if (url.pathname.endsWith('/sessions/S1/artifacts/plot.py')) {
        return new Response('import pandas as pd\n', { status: 200 });
      }
      if (url.pathname.includes('/sessions/S1/artifacts/')) {
        return new Response('png', { status: 200, headers: { 'Content-Type': 'image/png' } });
      }
      if (url.pathname.endsWith('/sessions/S1/feedback') && method === 'POST') {
        feedbackBodies.push(JSON.parse(String(init.body)));
        return feedbackAnswer();
      }
      if (url.pathname.endsWith('/debug/agent/status')) {
        return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true });
      }
      if (method === 'DELETE') return new Response(null, { status: 204 });
      return json(404, { detail: 'not_found' });
    })
  );
}

function renderPage() {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[PAGE]}>
        <AgentChatPage />
      </MemoryRouter>
    </ThemeProvider>
  );
}

/** Ask in the chat; the stub answers every turn with version 1. */
async function plotVersionOne() {
  const box = await screen.findByLabelText('Message');
  fireEvent.change(box, { target: { value: 'plot it' } });
  fireEvent.keyDown(box, { key: 'Enter' });
  return screen.findByRole('form', { name: 'Feedback on version 1' });
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem(ADMIN_HINT_KEY, '1');
  analytics.trackEvent.mockClear();
  wordsOnly = false;
  hold = null;
  feedbackAnswer = () =>
    json(201, {
      case_id: `20261012T14300${feedbackBodies.length}Z-1a2b3c4d`,
      stored: ['plot.py', 'manifest.json'],
    });
  URL.createObjectURL = vi.fn(() => 'blob:png');
  URL.revokeObjectURL = vi.fn();
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('AgentChatPage quick feedback', () => {
  it('offers feedback on the chat itself while the session has no plot', async () => {
    // The owner's case of 2026-10-12: a chat that never made a plot had nothing to report on.
    const user = userEvent.setup();
    wordsOnly = true;
    let release!: () => void;
    hold = new Promise<void>(resolve => {
      release = resolve;
    });
    renderPage();
    expect(screen.queryByTestId('chat-feedback')).not.toBeInTheDocument();
    const box = await screen.findByLabelText('Message');
    fireEvent.change(box, { target: { value: 'use y as the feature column' } });
    fireEvent.keyDown(box, { key: 'Enter' });
    // While the turn runs it may still bring the plot: no offer yet.
    await screen.findByText('use y as the feature column');
    expect(screen.queryByTestId('chat-feedback')).not.toBeInTheDocument();
    release();
    await screen.findByText('The feature role needs names, not numbers.');

    await user.click(await screen.findByRole('button', { name: 'Give feedback on this chat' }));
    const form = screen.getByRole('form', { name: 'Feedback on this chat' });
    // No data pasted: the box cannot be ticked.
    expect(
      within(form).getByRole('checkbox', { name: 'Include data.csv in the feedback on this chat' })
    ).toBeDisabled();
    await user.click(within(form).getByRole('button', { name: 'Idea' }));
    await user.click(within(form).getByRole('button', { name: 'Send feedback' }));

    await screen.findByText(/sent · this chat/);
    expect(feedbackBodies).toEqual([
      { reaction: 'idea', message: null, include_data: false, result_version: 0 },
    ]);
  });

  it('sends feedback on a version, shows it as sent, and sends an edit', async () => {
    const user = userEvent.setup();
    renderPage();
    const form = await plotVersionOne();

    await user.click(within(form).getByRole('button', { name: 'Thumbs down' }));
    await user.type(within(form).getByLabelText('Feedback message'), 'the legend hides points');
    expect(
      within(form).getByRole('checkbox', { name: 'Include data.csv in the feedback on version 1' })
    ).toBeChecked();
    await user.click(within(form).getByRole('button', { name: 'Send feedback' }));

    const sent = await screen.findByText(/sent · v1/);
    expect(sent).toHaveTextContent('sent · v1 · thumbs down · with data.csv');
    expect(feedbackBodies).toEqual([
      {
        reaction: 'thumbs_down',
        message: 'the legend hides points',
        include_data: true,
        result_version: 1,
      },
    ]);
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_result_feedback', {
      reaction: 'thumbs_down',
      include_data: 'yes',
      subject: 'result',
    });
    // Once a plot exists, its card takes the feedback: the chat's own control is gone.
    expect(screen.queryByTestId('chat-feedback')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit the feedback on version 1' }));
    await user.click(screen.getByRole('button', { name: 'Thumbs up' }));
    await user.click(screen.getByRole('button', { name: 'Send feedback' }));
    await waitFor(() =>
      expect(screen.getByText(/sent · v1/)).toHaveTextContent('sent · v1 · thumbs up')
    );
    expect(feedbackBodies).toHaveLength(2);
    // The edit names the case it replaces: the first answer's id.
    expect(feedbackBodies[1]).toMatchObject({
      reaction: 'thumbs_up',
      result_version: 1,
      replaces: '20261012T143001Z-1a2b3c4d',
    });
  });

  it('shows a failed send under the control and keeps the form', async () => {
    const user = userEvent.setup();
    feedbackAnswer = () => json(502, { detail: 'storage', ref: 'ref-st' });
    renderPage();
    const form = await plotVersionOne();

    await user.click(within(form).getByRole('button', { name: 'Bug' }));
    await user.click(within(form).getByRole('button', { name: 'Send feedback' }));

    expect(await within(form).findByRole('alert')).toHaveTextContent(
      'the case could not be stored; try again · ref ref-st'
    );
    expect(within(form).getByRole('button', { name: 'Bug' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    expect(analytics.trackEvent).not.toHaveBeenCalledWith(
      'agent_result_feedback',
      expect.anything()
    );
  });

  it('records a case stored without its row and names it in the next send', async () => {
    const user = userEvent.setup();
    const orphan = '20261012T150000Z-0badc0de';
    let answers = 0;
    feedbackAnswer = () =>
      answers++ === 0
        ? json(502, { detail: 'row_missing', ref: 'r-1', case_id: orphan })
        : json(201, { case_id: '20261012T150100Z-1a2b3c4d', stored: ['manifest.json'] });
    renderPage();
    const form = await plotVersionOne();

    await user.click(within(form).getByRole('button', { name: 'Thumbs up' }));
    await user.click(within(form).getByRole('button', { name: 'Send feedback' }));

    expect(await within(form).findByRole('alert')).toHaveTextContent(
      'the case is stored but not yet listed for triage; edit or resend names it · ref r-1'
    );
    // The form stays open; sending again replaces the stored case.
    await user.click(within(form).getByRole('button', { name: 'Send feedback' }));
    expect(await screen.findByText(/sent · v1/)).toHaveTextContent('sent · v1 · thumbs up');
    expect(feedbackBodies).toHaveLength(2);
    expect(feedbackBodies[0]).not.toHaveProperty('replaces');
    expect(feedbackBodies[1]).toMatchObject({ reaction: 'thumbs_up', replaces: orphan });
  });

  it('says that nothing was stored when the server is not ready', async () => {
    const user = userEvent.setup();
    feedbackAnswer = () => new Response(null, { status: 503 });
    renderPage();
    const form = await plotVersionOne();

    await user.click(within(form).getByRole('button', { name: 'Idea' }));
    await user.click(within(form).getByRole('button', { name: 'Send feedback' }));

    expect(await within(form).findByRole('alert')).toHaveTextContent(
      'the server is not ready; the case was not stored'
    );
  });
});
