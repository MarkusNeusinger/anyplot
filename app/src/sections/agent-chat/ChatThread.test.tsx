import { describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type PlotVersion,
  type RunState,
} from 'src/hooks/useAgentSession';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { localClock, REFUSAL_LABEL } from 'src/sections/agent-chat/messages';
import { awaitsReply, pendingReply } from 'src/sections/agent-chat/steps';
import { CHAT_TEXT_MAX } from 'src/sections/agent-chat/styles';
import { render, screen, userEvent, within } from 'src/test-utils';

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
        { id: 3, kind: 'notice', text: 'stopped' },
      ],
    });
    // A reply and a notice are no wider than about 80 characters (2026-11-02: the column grows
    // up to 1360 px); the user's turn keeps its right alignment. jsdom resolves `ch` to pixels
    // of each element's own font, so the check is that a cap is there, in `ch` or in pixels.
    expect(CHAT_TEXT_MAX).toBe('80ch');
    for (const element of [
      screen.getByText('Done: the markers are larger now.'),
      screen.getByText('# stopped'),
    ]) {
      expect(getComputedStyle(element).maxWidth).toMatch(/^\d+(\.\d+)?(px|ch)$/);
    }
    expect(getComputedStyle(screen.getByText('make the markers bigger')).alignSelf).toBe(
      'flex-end'
    );
  });

  it('reads a plot refused for an open role as a step to take', () => {
    // `data_unconfirmed` never comes here: the hook adds no item for it, the step line says it.
    renderThread(notReady('incomplete_bindings'));
    expect(screen.getByText('plot · not ready · incomplete_bindings')).toBeInTheDocument();
    expect(screen.getByText('pick a column for every required role first')).toBeInTheDocument();
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
    expect(paused).toHaveTextContent(`chat paused · until ${localClock(until)}${text}`);
    expect(own).toHaveTextContent(/^usage limit reachedThe usage limit/);
  });

  it('labels a refusal in plain words and keeps its code behind the ⓘ', async () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        { id: 1, kind: 'user', text: 'plot the unemployment rate of France' },
        { id: 2, kind: 'refusal', code: 'needs_data', text: 'I cannot fetch data.' },
        { id: 3, kind: 'refusal', code: 'something_new', text: 'No.' },
      ],
    });
    const [data, unknown] = screen.getAllByTestId('refusal');
    expect(data).toHaveTextContent(/^can't fetch dataI cannot fetch data\.$/);
    expect(unknown).toHaveTextContent(/^not answeredNo\.$/);
    // No code in the line itself: it reads behind the ⓘ.
    expect(screen.queryByText(/needs_data/)).not.toBeInTheDocument();
    await userEvent.click(within(data).getByRole('button', { name: 'About this answer' }));
    expect(await screen.findByTestId('refusal-details')).toHaveTextContent('reason: needs_data');
  });

  it('labels every refusal code of the service in plain words', () => {
    // Every refusal code of `refusals.yaml` (its `close_warning` is a suffix, never a code).
    for (const code of [
      'out_of_scope',
      'needs_data',
      'other_library',
      'unsupported_content',
      'budget',
      'service_paused',
      'rate_limited',
      'daily_limit',
      'session_closed',
      'locked_out',
    ]) {
      expect(REFUSAL_LABEL[code], code).toBeTruthy();
      expect(REFUSAL_LABEL[code]).not.toMatch(/_/);
    }
  });

  it("shows the page's own turns as the buttons pressed, and the summary, which has none, not at all", () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        { id: 1, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 2, kind: 'assistant', text: '12 rows and 3 columns.' },
        { id: 3, kind: 'action', action: 'create_plot', library: 'seaborn' },
        {
          id: 4,
          kind: 'action',
          action: 'create_plot',
          library: 'seaborn',
          label: '.start_over()',
        },
        // The carry after a switch from the plot button, which keeps its name.
        {
          id: 5,
          kind: 'action',
          action: 'carry_plot',
          library: 'plotly',
          label: '.create_plot()',
        },
        // A carry the chat started ("make it in plotly") has no button of its own.
        { id: 6, kind: 'action', action: 'carry_plot', library: 'plotly' },
        { id: 7, kind: 'action', action: 'example_data', library: 'plotly' },
      ],
    });
    const log = screen.getByRole('log');
    expect([...log.children].map(child => child.textContent)).toEqual([
      '12 rows and 3 columns.',
      '❯.create_plot()# seaborn',
      '❯.start_over()# seaborn',
      '❯.create_plot()# plotly',
      '❯plot in plotly with your decisions',
      '❯.example_data()',
    ]);
    expect(screen.queryByText(/summarize_data|carry_plot/)).not.toBeInTheDocument();
  });

  it('sets the passages of a reply in backticks off as code, without the backticks', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        {
          id: 1,
          kind: 'assistant',
          text: 'I read `Year` as dates; `.undo()` brings the text back. A lone ` stays.',
        },
      ],
    });
    const reply = screen.getByText(/brings the text back/);
    expect(reply).toHaveTextContent(
      'I read Year as dates; .undo() brings the text back. A lone ` stays.'
    );
    expect([...reply.querySelectorAll('code')].map(code => code.textContent)).toEqual([
      'Year',
      '.undo()',
    ]);
  });

  it('shows a stop as a quiet notice', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [{ id: 1, kind: 'notice', text: 'stopped' }],
    });
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
    // As in the progress timeline the line hands over to: the loader first, the words after it,
    // so the loader keeps its place when the timeline takes over.
    expect(pending.firstElementChild).toContainElement(
      within(pending).getByTestId('loader-spinner')
    );
    expect(pending.lastElementChild).toHaveTextContent(/^summarizing your data$/);
    // The section's gap above the timeline less the thread's own (2 - 1.5 spacing units of 8 px):
    // the timeline's top lands where this line's top was.
    expect(pending).toHaveStyle({ marginTop: '4px' });
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

  it("holds the reply's slot below a run's card until the reply takes it, at the thread's gap", () => {
    const plotPrompt: ChatItem = { id: 1, kind: 'action', action: 'create_plot', library: 'x' };
    const card: ChatItem = { id: 2, kind: 'plot', version: 1 };
    const plotRun = run({ kind: 'create_plot', steps: [{ step: 'reviewing', attempt: 1 }] });
    // The card is in, the reply is still being written: one line says so, a notice between them
    // or not.
    for (const items of [
      [plotPrompt, card],
      [plotPrompt, card, { id: 3, kind: 'notice', text: 'memory full' } as ChatItem],
    ]) {
      const { unmount } = renderThread(inFlight(items, plotRun));
      const pending = screen.getByTestId('pending-reply');
      expect(pending).toHaveTextContent(/^writing the reply$/);
      expect(screen.getByRole('log').lastElementChild).toBe(pending);
      // No timeline follows a card: the line keeps the thread's gap alone, where the reply goes,
      // one row of the reply's line height, so a one-line reply moves nothing below it.
      expect(pending).toHaveStyle({ marginTop: '0px', flexDirection: 'row', lineHeight: '1.6' });
      unmount();
    }
    // The card of a run that failed gets its reply too.
    const failed: ChatItem = {
      id: 2,
      kind: 'plot_failed',
      result: {
        status: 'failed',
        attempts: 2,
        artifacts: [],
        changes: [],
        residual_defects: [],
        version: null,
      },
    };
    expect(pendingReply(inFlight([plotPrompt, failed], plotRun))).toBe('writing');
    expect(pendingReply(inFlight([plotPrompt, card], { ...plotRun, stopping: true }))).toBe(
      'stopping'
    );
    // The reply arrived, or the run is over: the line is gone.
    const replied: ChatItem[] = [plotPrompt, card, { id: 3, kind: 'assistant', text: 'Done.' }];
    expect(pendingReply(inFlight(replied, plotRun))).toBeNull();
    expect(pendingReply(inFlight([plotPrompt, card], null))).toBeNull();
    // A card of an earlier run waits for nothing.
    expect(awaitsReply(inFlight([plotPrompt, card], null))).toBe(false);
  });

  it('names a message turn, and a stop before any step', () => {
    const asked: ChatItem[] = [{ id: 1, kind: 'user', text: 'what is on x?' }];
    const { unmount } = renderThread(inFlight(asked, run({ kind: 'message' })));
    expect(screen.getByTestId('pending-reply')).toHaveTextContent(/^working on your message$/);
    unmount();
    renderThread(inFlight(asked, run({ kind: 'message', stopping: true })));
    expect(screen.getByTestId('pending-reply')).toHaveTextContent(/^stopping$/);
  });

  it('says a cut stream reconnects, also after the reply arrived, and gives way to a stop', () => {
    const answered: ChatItem[] = [
      { id: 1, kind: 'user', text: 'what is on x?' },
      { id: 2, kind: 'assistant', text: 'Study Hours.' },
    ];
    const reconnecting = run({ kind: 'message', reconnecting: true });
    const { unmount } = renderThread(inFlight(answered, reconnecting));
    expect(screen.getByTestId('pending-reply')).toHaveTextContent(
      /^connection lost · reconnecting…$/
    );
    unmount();
    expect(pendingReply(inFlight(answered, { ...reconnecting, stopping: true }))).toBeNull();
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
    followReply: () => boolean = () => false,
    start?: React.ReactNode
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
        start={start}
      />
    );
  }

  it('puts the start item first, before the first turn, and keeps it there as the talk goes on', () => {
    const start = <div data-testid="start">You came from Basic Scatter Plot.</div>;
    const { rerender } = renderItems(ready([]), undefined, start);
    const log = screen.getByRole('log');
    // Before any turn the thread holds the start item alone.
    expect([...log.children].map(child => child.textContent)).toEqual([
      'You came from Basic Scatter Plot.',
    ]);
    rerender(
      <ChatThread
        state={ready([
          { id: 1, kind: 'paste', text: '▤ table · 3 lines · 46 B' },
          { id: 2, kind: 'data' },
          { id: 3, kind: 'assistant', text: '2 rows and 2 columns.' },
        ])}
        specId="scatter-basic"
        language="python"
        onRequestTheme={vi.fn()}
        onFetchArtifact={vi.fn()}
        onTrack={vi.fn()}
        renderData={renderData}
        start={start}
      />
    );
    expect([...log.children].map(child => child.textContent)).toEqual([
      'You came from Basic Scatter Plot.',
      '❯▤ table · 3 lines · 46 B',
      'data card',
      '2 rows and 2 columns.',
    ]);
  });

  it('shows the paste, its card and a stub in thread order, without the summary action after the card', () => {
    renderItems(
      ready([
        { id: 1, kind: 'paste', text: '▤ table · 3 lines · 46 B' },
        { id: 2, kind: 'data_stub', rows: 1203, columns: 4 },
        { id: 3, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
        { id: 4, kind: 'assistant', text: '1,203 rows and 4 columns.' },
        { id: 5, kind: 'paste', text: '▤ sales.csv · 8 lines · 120 B' },
        { id: 6, kind: 'data' },
        // A notice between card and summary (the reply language a paste set, say) is no turn.
        { id: 7, kind: 'notice', text: 'reply language: en' },
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
      '# reply language: en',
      '7 rows and 3 columns.',
    ]);
  });

  it('shows no summary action that does not follow a card either, and the card of a table that waits', () => {
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

describe('ChatThread plot cards', () => {
  const version = (number: number): PlotVersion => ({
    number,
    library: 'matplotlib',
    theme: 'light',
    result: {
      status: 'ok',
      reason: null,
      attempts: 1,
      artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
      changes: [],
      residual_defects: [],
      version: number,
    },
    images: {
      light: { state: 'ready', url: `blob:v${number}`, blob: new Blob(['png']), status: 'ok' },
    },
    code: { state: 'ready', text: 'print(1)\n' },
  });

  it('labels each plot with what it answered, and folds every version but the latest', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      versions: { 1: version(1), 2: version(2) },
      items: [
        {
          id: 1,
          kind: 'action',
          action: 'create_plot',
          library: 'matplotlib',
          label: '.create_plot() →',
        },
        { id: 2, kind: 'plot', version: 1 },
        {
          id: 3,
          kind: 'user',
          text: 'put the title in German and make the markers twice as large',
        },
        { id: 4, kind: 'plot', version: 2 },
      ],
    });
    const older = screen.getByRole('button', { name: 'Plot version 1, matplotlib, first plot' });
    expect(older).toHaveTextContent(/^▸plot v1 · matplotlib · first plot$/);
    expect(older).toHaveAttribute('aria-expanded', 'false');
    // The latest is open under its label, the request cut to 40 characters.
    const latest = screen.getByRole('button', {
      name: 'Plot version 2, matplotlib, put the title in German and make the ma…',
    });
    expect(latest).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getAllByRole('img').map(image => image.getAttribute('alt'))).toEqual([
      'Adapted plot, version 2, light theme',
    ]);
  });
});
