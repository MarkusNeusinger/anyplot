import { describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { localClock } from 'src/sections/agent-chat/messages';
import { pendingReply } from 'src/sections/agent-chat/steps';
import { CHAT_TEXT_MAX } from 'src/sections/agent-chat/styles';
import { render, screen, within } from 'src/test-utils';

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
  it("keeps the thread's text to a readable line in the wide column", () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        { id: 1, kind: 'user', text: 'make the markers bigger' },
        { id: 2, kind: 'assistant', text: 'Done: the markers are larger now.' },
        { id: 3, kind: 'notice', text: 'bindings changed', tone: 'warning' },
      ],
    });
    // A reply and a notice are no wider than about 80 characters (2026-11-02: the column grows
    // up to 1360 px); the user's turn keeps its right alignment. jsdom resolves `ch` to pixels
    // of each element's own font, so the check is that a cap is there, in `ch` or in pixels.
    expect(CHAT_TEXT_MAX).toBe('80ch');
    for (const element of [
      screen.getByText('Done: the markers are larger now.'),
      screen.getByTestId('confirm-lost'),
    ]) {
      expect(getComputedStyle(element).maxWidth).toMatch(/^\d+(\.\d+)?(px|ch)$/);
    }
    expect(getComputedStyle(screen.getByText('make the markers bigger')).alignSelf).toBe(
      'flex-end'
    );
  });

  it('reads a plot refused for unconfirmed data as a step to take', () => {
    renderThread(notReady('data_unconfirmed'));
    expect(screen.getByText('plot · not ready · data_unconfirmed')).toBeInTheDocument();
    expect(
      screen.getByText(
        'the data is not confirmed: check the preview and the bindings, then .create_plot()'
      )
    ).toBeInTheDocument();
  });

  it('keeps a generic line for a reason it does not know', () => {
    renderThread(notReady('something_new'));
    expect(screen.getByText('no plot this time')).toBeInTheDocument();
  });

  it("adds the user's own time to the service's pause, which names only UTC", () => {
    const until = '2026-11-03T00:00:00.000Z';
    const text =
      "The chat has reached today's overall limit and is paused until 00:00 UTC. Your own limit is not affected.";
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        { id: 1, kind: 'user', text: 'log scale on y' },
        { id: 2, kind: 'refusal', code: 'service_paused', text, until },
        { id: 3, kind: 'refusal', code: 'budget', text: 'The usage limit for now is reached.' },
      ],
    });
    const [paused, own] = screen.getAllByTestId('refusal');
    expect(paused).toHaveTextContent(
      `refusal · service_paused · until ${localClock(until)}${text}`
    );
    expect(own).toHaveTextContent(/^refusal · budgetThe usage limit/);
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
          text: 'bindings changed · check them, then .create_plot()',
        },
        { id: 2, kind: 'notice', text: 'stopped' },
      ],
    });
    expect(screen.getByTestId('confirm-lost')).toHaveTextContent(
      '# bindings changed · check them, then .create_plot()'
    );
    expect(screen.getAllByTestId('confirm-lost')).toHaveLength(1);
    expect(screen.getByText('# stopped')).toBeInTheDocument();
  });

  it("says in plain words that the user's other windows hold their runs, without a number of its own", () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [{ id: 1, kind: 'error', code: 'run_limit', ref: 'r-lim' }],
    });
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('error · run_limit · ref r-lim');
    // The cap is the caller's own (2, or 5 for an admin), or on the public lane the network's,
    // so the sentence names no number.
    expect(alert).toHaveTextContent(
      'your plots and data runs in other windows, or others on your network, already fill the share; wait until one finishes, then try again'
    );
  });

  it('reads a run the model service refused for its quota as busy, not as a fault', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        {
          id: 1,
          kind: 'plot_failed',
          result: {
            status: 'failed',
            reason: 'busy',
            attempts: 1,
            artifacts: [],
            changes: [],
            residual_defects: [],
            version: null,
          },
        },
      ],
    });
    expect(
      screen.getByText(/the model service is busy; try again in a minute/)
    ).toBeInTheDocument();
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
    expect(pending).toHaveTextContent(/^summarizing your data$/);
    // The site's loader beside the words, hidden from screen readers, which read the words.
    expect(within(pending).getByTestId('loader-spinner')).toHaveAttribute('aria-hidden', 'true');
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
    expect(screen.getByTestId('pending-reply')).toHaveTextContent(/^working on your message$/);
    unmount();
    renderThread(inFlight(asked, run({ kind: 'message', stopping: true })));
    expect(screen.getByTestId('pending-reply')).toHaveTextContent(/^stopping$/);
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

describe('ChatThread data items', () => {
  const ready = (items: ChatItem[], overrides: Partial<AgentSessionState> = {}) => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready' as const,
    sessionId: 'S1',
    items,
    ...overrides,
  });
  const renderData = (part: 'data' | 'transcription') => (
    <div data-testid={`rendered-${part}`}>{part} card</div>
  );

  function renderItems(
    state: AgentSessionState,
    followReply: () => boolean = () => false
  ): ReturnType<typeof render> {
    return render(
      <ChatThread
        state={state}
        specId="scatter-basic"
        language="python"
        onRequestTheme={vi.fn()}
        onFetchArtifact={vi.fn()}
        onTrack={vi.fn()}
        renderData={renderData}
        followReply={followReply}
      />
    );
  }

  it('shows the paste, its card and a stub in thread order, without the summary action after the card', () => {
    renderItems(
      ready([
        { id: 1, kind: 'paste', text: '▤ table · 3 lines · 46 B' },
        { id: 2, kind: 'data_stub', rows: 1203, columns: 4 },
        { id: 3, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 4, kind: 'assistant', text: '1,203 rows and 4 columns.' },
        { id: 5, kind: 'paste', text: '▤ sales.csv · 8 lines · 120 B' },
        { id: 6, kind: 'data' },
        // A paste in step 2 drops the confirmation: its notice stands between card and summary.
        { id: 7, kind: 'notice', tone: 'warning', text: 'the data changed' },
        { id: 8, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 9, kind: 'assistant', text: '7 rows and 3 columns.' },
      ])
    );
    const log = screen.getByRole('log');
    // Neither summary action shows: the stub is the card it followed, and a notice is no turn.
    expect([...log.children].map(child => child.textContent)).toEqual([
      '❯▤ table · 3 lines · 46 B',
      '# earlier data · 1,203 rows · 4 columns · replaced below',
      '1,203 rows and 4 columns.',
      '❯▤ sales.csv · 8 lines · 120 B',
      'data card',
      '# the data changed',
      '7 rows and 3 columns.',
    ]);
  });

  it('keeps a summary action that does not follow a card, and the card of a table that waits', () => {
    const waiting = ready(
      [
        { id: 1, kind: 'transcription' },
        { id: 2, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 3, kind: 'transcription' },
      ],
      {
        transcription: {
          text: 'a,b\n1,2\n',
          preview: [['1', '2']],
          profile: { rows: 1, columns: [], source_format: 'csv', decimal: '.', warnings: [] },
          warnings: [],
          note: '',
          bytes: 8,
        },
      }
    );
    renderItems(waiting);
    const log = screen.getByRole('log');
    expect([...log.children].map(child => child.textContent)).toEqual([
      // An older table read from text that a new paste dropped; only the latest one waits.
      '# table read from text · not used',
      '❯.summarize_data()',
      'transcription card',
    ]);
  });

  it('brings the first reply after a card into view once, only while the focus is in the composer', () => {
    const scroll = vi.fn();
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      value: scroll,
      configurable: true,
      writable: true,
    });
    try {
      const card: ChatItem[] = [
        { id: 1, kind: 'paste', text: '▤ table' },
        { id: 2, kind: 'data' },
        { id: 3, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
      ];
      let atComposer = true;
      // A thread that mounts with its reply already there leaves the page where it is.
      const mounted = renderItems(
        ready([...card, { id: 4, kind: 'assistant', text: '4 rows.' }]),
        () => true
      );
      expect(scroll).not.toHaveBeenCalled();
      mounted.unmount();

      const { rerender } = renderItems(ready(card), () => atComposer);
      expect(scroll).not.toHaveBeenCalled();
      const thread = (items: ChatItem[]) => (
        <ChatThread
          state={ready(items)}
          specId="scatter-basic"
          language="python"
          onRequestTheme={vi.fn()}
          onFetchArtifact={vi.fn()}
          onTrack={vi.fn()}
          renderData={renderData}
          followReply={() => atComposer}
        />
      );
      const replied: ChatItem[] = [...card, { id: 4, kind: 'assistant', text: '4 rows.' }];
      rerender(thread(replied));
      expect(scroll.mock.contexts).toEqual([screen.getByTestId('first-reply')]);
      expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'nearest' });
      // A second reply is no first reply; the first one scrolled once.
      rerender(thread([...replied, { id: 5, kind: 'assistant', text: 'And a note.' }]));
      expect(scroll).toHaveBeenCalledTimes(1);

      // Read elsewhere on the page, the reply to the next card stays where it lands.
      atComposer = false;
      const next: ChatItem[] = [
        ...replied,
        { id: 6, kind: 'paste', text: '▤ table' },
        { id: 7, kind: 'data' },
        { id: 8, kind: 'assistant', text: '5 rows.' },
      ];
      rerender(thread(next));
      expect(scroll).toHaveBeenCalledTimes(1);
    } finally {
      delete (Element.prototype as Partial<Element>).scrollIntoView;
    }
  });
});
