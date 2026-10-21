import { describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { pendingReply } from 'src/sections/agent-chat/steps';
import { render, screen } from 'src/test-utils';

const notReady = (reason: string): AgentSessionState => ({
  ...initialAgentState('matplotlib'),
  phase: 'ready',
  sessionId: 'S1',
  items: [
    { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' },
    {
      id: 2,
      kind: 'plot_failed',
      result: {
        status: 'not_ready',
        reason,
        attempts: 0,
        artifacts: [],
        changes: [],
        residual_defects: [],
        version: null,
      },
    },
  ],
});

function renderThread(state: AgentSessionState) {
  return render(
    <ChatThread
      state={state}
      specId="scatter-basic"
      language="python"
      onRequestTheme={vi.fn()}
      onFetchArtifact={vi.fn()}
      onTrack={vi.fn()}
    />
  );
}

describe('ChatThread', () => {
  it('reads a plot refused for unconfirmed data as a step to take', () => {
    renderThread(notReady('data_unconfirmed'));
    expect(screen.getByText('plot · not ready · data_unconfirmed')).toBeInTheDocument();
    expect(
      screen.getByText(
        'confirm your data first: check the preview and the bindings, then .confirm()'
      )
    ).toBeInTheDocument();
  });

  it('keeps a generic line for a reason it does not know', () => {
    renderThread(notReady('something_new'));
    expect(screen.getByText('no plot this time')).toBeInTheDocument();
  });

  it("shows the page's own turns: the summary without a library, create_plot with it", () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        { id: 1, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 2, kind: 'assistant', text: '12 rows and 3 columns.' },
        { id: 3, kind: 'action', action: 'create_plot', library: 'seaborn' },
      ],
    });
    const log = screen.getByRole('log');
    expect(log.children[0]).toHaveTextContent(/^❯\.summarize_data\(\)$/);
    expect(log.children[1]).toHaveTextContent('12 rows and 3 columns.');
    expect(log.children[2]).toHaveTextContent(/^❯\.create_plot\(\)# seaborn$/);
  });

  it('shows a lost confirmation as a warning notice, and a stop as a plain one', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        {
          id: 1,
          kind: 'notice',
          tone: 'warning',
          text: 'bindings changed · confirm the data again',
        },
        { id: 2, kind: 'notice', text: 'stopped' },
      ],
    });
    expect(screen.getByTestId('confirm-lost')).toHaveTextContent(
      '# bindings changed · confirm the data again'
    );
    expect(screen.getAllByTestId('confirm-lost')).toHaveLength(1);
    expect(screen.getByText('# stopped')).toBeInTheDocument();
  });

  it("says in plain words that the user's other windows hold their three runs", () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [{ id: 1, kind: 'error', code: 'run_limit', ref: 'r-lim' }],
    });
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('error · run_limit · ref r-lim');
    expect(alert).toHaveTextContent(
      'you already have 3 plots or data runs in progress in other windows; wait until one finishes, then try again'
    );
  });

  it('names this window, not the others, for a run_active turn', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [{ id: 1, kind: 'error', code: 'run_active', ref: null }],
    });
    expect(screen.getByRole('alert')).toHaveTextContent(
      'a run, a theme render or a paste is still in progress in this window'
    );
  });
});

describe('ChatThread in-progress line', () => {
  const run = (overrides: Partial<RunState> = {}): RunState => ({
    kind: 'summarize_data',
    steps: [],
    queue: null,
    stopping: false,
    ...overrides,
  });
  const summaryPrompt: ChatItem = {
    id: 1,
    kind: 'action',
    action: 'summarize_data',
    library: 'matplotlib',
  };
  const inFlight = (items: ChatItem[], current: RunState | null): AgentSessionState => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    items,
    run: current,
  });

  it("holds the assistant's slot while the summary is written, as the log's last entry", () => {
    const state = inFlight([summaryPrompt], run());
    expect(pendingReply(state)).toBe('summarize_data');
    renderThread(state);
    const pending = screen.getByTestId('pending-reply');
    expect(pending).toHaveTextContent('summarizing your data …');
    expect(screen.getByRole('log').lastElementChild).toBe(pending);
  });

  it('gives way to the reply', () => {
    const state = inFlight(
      [summaryPrompt, { id: 2, kind: 'assistant', text: '2 rows and 2 columns.' }],
      run()
    );
    expect(pendingReply(state)).toBeNull();
    renderThread(state);
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
  });

  it('names a message turn, and a stop before any step', () => {
    const asked: ChatItem[] = [{ id: 1, kind: 'user', text: 'what is on x?' }];
    const { unmount } = renderThread(inFlight(asked, run({ kind: 'message' })));
    expect(screen.getByTestId('pending-reply')).toHaveTextContent('working on your message …');
    unmount();
    renderThread(inFlight(asked, run({ kind: 'message', stopping: true })));
    expect(screen.getByTestId('pending-reply')).toHaveTextContent('stopping …');
  });

  it('leaves a plot run and a pipeline step to the progress timeline, and keeps a queue wait', () => {
    const plotPrompt: ChatItem = {
      id: 1,
      kind: 'action',
      action: 'create_plot',
      library: 'matplotlib',
    };
    expect(pendingReply(inFlight([plotPrompt], run({ kind: 'create_plot' })))).toBeNull();
    const asked: ChatItem[] = [{ id: 1, kind: 'user', text: 'log scale on y' }];
    const queued = { step: 'queued' as const, attempt: null };
    // The queue counter says where the turn waits; the line still says what it is.
    expect(pendingReply(inFlight(asked, run({ kind: 'message', steps: [queued] })))).toBe(
      'message'
    );
    expect(
      pendingReply(
        inFlight(asked, run({ kind: 'message', steps: [queued, { step: 'adapting', attempt: 1 }] }))
      )
    ).toBeNull();
    // No run, no line.
    expect(pendingReply(inFlight(asked, null))).toBeNull();
    renderThread(inFlight([plotPrompt], run({ kind: 'create_plot' })));
    expect(screen.queryByTestId('pending-reply')).not.toBeInTheDocument();
  });
});
