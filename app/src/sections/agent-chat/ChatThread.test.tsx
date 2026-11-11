import { useState } from 'react';

import { describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  type DataSnapshot,
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
    // The row the bubble stands in, which also holds a question's mark beside it.
    const turn = screen.getByText('make the markers bigger').parentElement!;
    expect(turn).toHaveAttribute('data-testid', 'user-turn');
    expect(getComputedStyle(turn).alignSelf).toBe('flex-end');
    expect(getComputedStyle(turn).maxWidth).toMatch(/\S/);
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
    // The chapters follow the turns: the summary is about the data, the plot buttons about the
    // plot, and example data about the data again.
    expect([...log.children].map(child => child.textContent)).toEqual([
      '# data',
      '12 rows and 3 columns.',
      '# plot',
      '❯.create_plot()# seaborn',
      '❯.start_over()# seaborn',
      '❯.create_plot()# plotly',
      '❯plot in plotly with your decisions',
      '# data',
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

  it('sets the passages of a reply between asterisk pairs off as strong, never inside a word or code', () => {
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      items: [
        {
          id: 1,
          kind: 'assistant',
          text:
            '**Total: 1,716** over 9 rows, (**net**) of returns.\n' +
            '**Next:** check `2**10` and a**b**c; 2 ** 3 and ** alone ** stay, so does **open.',
        },
      ],
    });
    const reply = screen.getByText(/over 9 rows/);
    expect(reply).toHaveTextContent(
      'Total: 1,716 over 9 rows, (net) of returns. Next: check 2**10 and a**b**c; 2 ** 3 and ** alone ** stay, so does **open.'
    );
    expect([...reply.querySelectorAll('strong')].map(strong => strong.textContent)).toEqual([
      'Total: 1,716',
      'net',
      'Next:',
    ]);
    expect([...reply.querySelectorAll('code')].map(code => code.textContent)).toEqual(['2**10']);
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

describe('ChatThread working line', () => {
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
  /** A reply's line height, resolved to pixels as a browser does: the bar for the working line. */
  const replyLineHeight = () => {
    const reply = renderThread(
      inFlight([summaryPrompt, { id: 2, kind: 'assistant', text: 'Done.' }], null)
    );
    const lineHeight = getComputedStyle(screen.getByText('Done.')).lineHeight;
    reply.unmount();
    expect(lineHeight).toMatch(/^\d+(\.\d+)?px$/);
    return lineHeight;
  };

  it("holds the assistant's slot while the summary is written, as the log's last entry", () => {
    const lineHeight = replyLineHeight();
    const state = inFlight([summaryPrompt], run());
    expect(pendingReply(state)).toBe('summarize_data');
    renderThread(state);
    const pending = screen.getByTestId('working-line');
    expect(pending).toHaveTextContent(/^summarizing your data$/);
    // The site's loader beside the words, hidden from screen readers, which read the words.
    expect(within(pending).getByTestId('loader-spinner')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByRole('log').lastElementChild).toBe(pending);
    // The loader first, the words after it, in the reply's line height: a turn that turns into
    // plot work changes only the words, and the reply takes the line's place without a jump.
    expect(pending.firstElementChild).toContainElement(
      within(pending).getByTestId('loader-spinner')
    );
    expect(pending.lastElementChild).toHaveTextContent(/^summarizing your data$/);
    expect(pending).toHaveStyle({ lineHeight });
  });

  it('gives way to the reply', () => {
    const state = inFlight(
      [summaryPrompt, { id: 2, kind: 'assistant', text: '2 rows and 2 columns.' }],
      run()
    );
    expect(pendingReply(state)).toBeNull();
    renderThread(state);
    expect(screen.queryByTestId('working-line')).not.toBeInTheDocument();
  });

  it("holds the reply's slot below a run's card until the reply takes it, at the thread's gap", () => {
    const plotPrompt: ChatItem = { id: 1, kind: 'action', action: 'create_plot', library: 'x' };
    const card: ChatItem = { id: 2, kind: 'plot', version: 1 };
    const plotRun = run({ kind: 'create_plot', steps: [{ step: 'reviewing', attempt: 1 }] });
    const lineHeight = replyLineHeight();
    // The card is in, the reply is still being written: one line says so, a notice between them
    // or not.
    for (const items of [
      [plotPrompt, card],
      [plotPrompt, card, { id: 3, kind: 'notice', text: 'memory full' } as ChatItem],
    ]) {
      const { unmount } = renderThread(inFlight(items, plotRun));
      const pending = screen.getByTestId('working-line');
      expect(pending).toHaveTextContent(/^writing the reply$/);
      expect(screen.getByRole('log').lastElementChild).toBe(pending);
      // The line keeps the thread's gap alone, where the reply goes, in the reply's line height,
      // so a one-line reply moves nothing below it.
      expect(pending).toHaveStyle({ lineHeight });
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
    expect(screen.getByTestId('working-line')).toHaveTextContent(/^working on your message$/);
    unmount();
    renderThread(inFlight(asked, run({ kind: 'message', stopping: true })));
    expect(screen.getByTestId('working-line')).toHaveTextContent(/^stopping…$/);
  });

  it('says a cut stream reconnects, also after the reply arrived, and gives way to a stop', () => {
    const answered: ChatItem[] = [
      { id: 1, kind: 'user', text: 'what is on x?' },
      { id: 2, kind: 'assistant', text: 'Study Hours.' },
    ];
    const reconnecting = run({ kind: 'message', reconnecting: true });
    const { unmount } = renderThread(inFlight(answered, reconnecting));
    expect(screen.getByTestId('working-line')).toHaveTextContent(
      /^connection lost · reconnecting…$/
    );
    unmount();
    expect(pendingReply(inFlight(answered, { ...reconnecting, stopping: true }))).toBeNull();
  });

  it('draws a plot run and a turn that reached a pipeline step on the same line, with its clock', () => {
    vi.useFakeTimers({ now: Date.UTC(2026, 10, 9, 12) });
    try {
      const plotPrompt: ChatItem = {
        id: 1,
        kind: 'action',
        action: 'create_plot',
        library: 'matplotlib',
      };
      const startedAt = Date.now() - 42_000;
      const { unmount } = renderThread(
        inFlight([plotPrompt], run({ kind: 'create_plot', startedAt }))
      );
      const line = screen.getByTestId('working-line');
      expect(line).toHaveTextContent(/^drawing your plot · 0:42$/);
      expect(line).toHaveAttribute('data-kind', 'drawing');
      expect(screen.getByRole('log').lastElementChild).toBe(line);
      // One element, one place: the second try changes its words only.
      expect(within(line).getByTestId('run-clock')).toHaveAttribute('aria-hidden', 'true');
      unmount();
      const asked: ChatItem[] = [{ id: 1, kind: 'user', text: 'log scale on y' }];
      const queued = { step: 'queued' as const, attempt: null };
      // The own turn in the queue: the line says where, and no clock runs while it waits.
      const waiting = renderThread(
        inFlight(
          asked,
          run({ kind: 'message', steps: [queued], queue: { position: 2, waiting: 4 }, startedAt })
        )
      );
      expect(screen.getByTestId('working-line')).toHaveTextContent(/^waiting · you are 2nd$/);
      expect(screen.queryByTestId('run-clock')).not.toBeInTheDocument();
      waiting.unmount();
      renderThread(
        inFlight(
          asked,
          run({
            kind: 'message',
            steps: [
              { step: 'adapting', attempt: 1 },
              { step: 'repairing', attempt: 2 },
            ],
            maxAttempts: 2,
            startedAt,
          })
        )
      );
      expect(screen.getByTestId('working-line')).toHaveTextContent(
        /^drawing your plot · try 2 of 2 · 0:42$/
      );
      // No run, no line.
      expect(pendingReply(inFlight(asked, null))).toBeNull();
    } finally {
      vi.useRealTimers();
    }
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
  /**
   * The items after a turn's data version, as the reducer places it: a stub where the card
   * stood, the card right after the turn's message (the fourth item), before its reply.
   */
  const moved = (before: ChatItem[]): ChatItem[] => [
    before[0],
    { id: 6, kind: 'data_stub', rows: 4, columns: 2, card: 2 },
    before[2],
    before[3],
    { id: 2, kind: 'data' },
    before[4],
  ];

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
      '# data',
      '❯▤ table · 3 lines · 46 B',
      'data card',
      '2 rows and 2 columns.',
    ]);
  });

  it('shows the paste, its card and a stub in thread order, without the summary action after the card', () => {
    renderItems(
      ready([
        { id: 1, kind: 'paste', text: '▤ table · 3 lines · 46 B' },
        // A stub a hand-built thread gives no snapshot: a quiet line of its shape.
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
    // Neither summary action shows, and a notice is no turn: one data chapter.
    expect([...log.children].map(child => child.textContent)).toEqual([
      '# data',
      '❯▤ table · 3 lines · 46 B',
      'data · 1,203 rows × 4 cols',
      '1,203 rows and 4 columns.',
      '❯▤ sales.csv · 8 lines · 120 B',
      'data card',
      '# reply language: en',
      '7 rows and 3 columns.',
    ]);
  });

  it('folds an older data version to its label, which opens it read-only', async () => {
    const snapshot: DataSnapshot = {
      n: 2,
      change: 'sheet',
      summary: 'sheet "2026"',
      label: 'data v2 · sheet "2026"',
      rows: 12,
      columns: 2,
      sheet: '2026',
      fileName: 'Bericht.xlsx',
      changes: ['dropped 1 row where Region = Total'],
      preview: [['North', '4210']],
      profile: {
        rows: 12,
        columns: [
          { name: 'Region', dtype: 'text', missing: 0, unique: 12 },
          { name: 'Q1', dtype: 'integer', missing: 0, unique: 12 },
        ],
        source_format: 'csv',
        decimal: '.',
        warnings: [],
      },
    };
    renderItems(
      ready([
        { id: 1, kind: 'paste', text: '▤ Bericht.xlsx' },
        { id: 3, kind: 'data_stub', rows: 12, columns: 2, snapshot, card: 2 },
        { id: 2, kind: 'data' },
      ])
    );
    const toggle = screen.getByRole('button', {
      name: 'Data v2, sheet "2026", 12 rows by 2 columns',
    });
    expect(toggle).toHaveTextContent(/^▸data v2 · sheet "2026" · 12 rows × 2 cols$/);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    const stub = screen.getByTestId('data-stub');
    expect(within(stub).queryByRole('table')).not.toBeInTheDocument();

    await userEvent.click(toggle);
    // The same button, open: what the version held, from its snapshot, and nothing to press.
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(toggle).toHaveFocus();
    expect(within(stub).getByTestId('folded-data-changes')).toHaveTextContent(
      '# changeddropped 1 row where Region = Total'
    );
    expect(within(stub).getByTestId('folded-data-source')).toHaveTextContent(
      'read as csv · from "Bericht.xlsx" · sheet "2026"'
    );
    expect(within(stub).getByRole('columnheader', { name: /^Q1/ })).toHaveTextContent(
      'Q1 · number'
    );
    expect(within(stub).getByRole('cell', { name: '4210' })).toBeInTheDocument();
    expect(within(stub).getAllByRole('button')).toEqual([toggle]);
    expect(within(stub).queryByRole('combobox')).not.toBeInTheDocument();

    await userEvent.click(toggle);
    expect(within(stub).queryByRole('table')).not.toBeInTheDocument();
    // Each version is a card of its own, named as a plot card is.
    expect(screen.getByRole('article', { name: 'Data version 2' })).toBe(stub);
  });

  it('says a file name the content check withheld as withheld, as the live card does', async () => {
    const withheld = {
      n: 1,
      change: 'paste',
      summary: 'pasted',
      label: 'data v1 · pasted',
      rows: 1,
      columns: 1,
      sheet: null,
      fileName: '(name withheld)',
      changes: [],
      preview: [['1']],
      profile: {
        rows: 1,
        columns: [{ name: 'a', dtype: 'integer', missing: 0, unique: 1 }],
        source_format: 'csv',
        decimal: '.',
        warnings: [],
      },
    } satisfies DataSnapshot;
    renderItems(
      ready([
        { id: 1, kind: 'data_stub', rows: 1, columns: 1, snapshot: withheld, card: 2 },
        { id: 2, kind: 'data' },
      ])
    );
    await userEvent.click(screen.getByTestId('data-stub-label'));
    expect(screen.getByTestId('folded-data-source')).toHaveTextContent(
      /^read as csv · from a file, name withheld by the content check$/
    );
  });

  it('opens a chapter where the step changes, and a library switch is a line of its own', () => {
    renderItems(
      ready([
        { id: 1, kind: 'paste', text: '▤ table' },
        { id: 2, kind: 'data' },
        { id: 3, kind: 'action', action: 'create_plot', library: 'matplotlib' },
        { id: 4, kind: 'assistant', text: 'Plot 1.' },
        { id: 5, kind: 'switch', from: 'matplotlib', library: 'seaborn', decisions: 3 },
        {
          id: 6,
          kind: 'action',
          action: 'carry_plot',
          library: 'seaborn',
          label: '.update_plot() →',
        },
        { id: 7, kind: 'switch', from: 'seaborn', library: 'plotly', decisions: null },
        { id: 8, kind: 'switch', from: 'plotly', library: 'bokeh', decisions: 1 },
        { id: 9, kind: 'user', text: 'only 2026, please' },
        { id: 10, kind: 'assistant', text: 'Kept 2026.' },
      ])
    );
    const log = screen.getByRole('log');
    expect([...log.children].map(child => child.textContent)).toEqual([
      '# data',
      '❯▤ table',
      'data card',
      '# plot',
      '❯.create_plot()# matplotlib',
      'Plot 1.',
      '· plotting in seaborn from here, 3 decisions kept',
      '❯.update_plot() →# seaborn',
      // A switch without an offer names no count, never "0 decisions".
      '· plotting in plotly from here',
      '· plotting in bokeh from here, 1 decision kept',
      // A question changes no step: it stays in the plot chapter.
      '❯only 2026, please',
      'Kept 2026.',
    ]);
    // The chapter lines are headings, the comment mark not read out.
    expect(
      screen.getAllByRole('heading', { level: 3 }).map(heading => heading.textContent)
    ).toEqual(['# data', '# plot']);
    expect(within(screen.getAllByRole('heading')[0]).getByText('#')).toHaveAttribute('aria-hidden');
  });

  it('keeps a reply its element when the card moves below it, so the log reads it once', () => {
    const thread = (items: ChatItem[]) => (
      <ChatThread
        state={ready(items)}
        specId="scatter-basic"
        language="python"
        onRequestTheme={vi.fn()}
        onFetchArtifact={vi.fn()}
        onTrack={vi.fn()}
        renderData={renderData}
      />
    );
    const before: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      { id: 2, kind: 'data' },
      { id: 3, kind: 'assistant', text: '4 rows.' },
      { id: 4, kind: 'user', text: 'only 2026' },
      { id: 5, kind: 'assistant', text: 'Kept 2026.' },
    ];
    const { rerender } = render(thread(before));
    const summary = screen.getByText('4 rows.');
    expect(screen.getByTestId('first-reply')).toContainElement(summary);
    // The turn's version moves the card in front of the turn's reply: the summary is no first
    // reply now, and stays the same node; the turn's reply is the first one.
    rerender(thread(moved(before)));
    expect(screen.getByText('4 rows.')).toBe(summary);
    expect(screen.getByTestId('first-reply')).toHaveTextContent('Kept 2026.');
  });

  it('holds the reply still when the card lands above it, unless it stands below the window', async () => {
    const thread = (items: ChatItem[]) => (
      <ChatThread
        state={ready(items)}
        specId="scatter-basic"
        language="python"
        onRequestTheme={vi.fn()}
        onFetchArtifact={vi.fn()}
        onTrack={vi.fn()}
        renderData={renderData}
      />
    );
    const before: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      { id: 2, kind: 'data' },
      { id: 3, kind: 'assistant', text: '4 rows.' },
      { id: 4, kind: 'user', text: 'only 2026' },
      { id: 5, kind: 'assistant', text: 'Kept 2026.' },
    ];
    // jsdom lays nothing out: the turn's reply stands at `top`, 240 px lower once the card is in
    // front of it.
    let top = 600;
    const rect = vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(function (
      this: Element
    ) {
      const reply = this.getAttribute('data-reply') === '5';
      const below = this.previousElementSibling?.getAttribute('data-testid') === 'rendered-data';
      return { top: reply ? top + (below ? 240 : 0) : 0 } as DOMRect;
    });
    // An earlier test's frame may still hold the anchoring: let it run first.
    await new Promise(resolve => setTimeout(resolve, 50));
    const page = document.documentElement.style.overflowAnchor;
    let during = '';
    const scrollBy = vi.spyOn(window, 'scrollBy').mockImplementation(() => {
      during = document.documentElement.style.overflowAnchor;
    });
    const frame = vi.spyOn(window, 'requestAnimationFrame').mockImplementation(callback => {
      callback(0);
      return 0;
    });
    try {
      const { rerender, unmount } = render(thread(before));
      rerender(thread(moved(before)));
      // The page scrolls by the distance the reply moved, with the browser's anchoring off for
      // that commit and back to the page's own value after it.
      expect(scrollBy).toHaveBeenCalledWith({ top: 240, behavior: 'instant' });
      expect(during).toBe('none');
      expect(document.documentElement.style.overflowAnchor).toBe(page);
      unmount();

      // A reply below the window's bottom edge is not being read: it lands where it lands.
      top = window.innerHeight + 10;
      scrollBy.mockClear();
      const again = render(thread(before));
      again.rerender(thread(moved(before)));
      expect(scrollBy).not.toHaveBeenCalled();
    } finally {
      rect.mockRestore();
      scrollBy.mockRestore();
      frame.mockRestore();
    }
  });

  it('keeps the live card mounted with its own state when a version moves it into a new chapter', async () => {
    function Card() {
      const [open, setOpen] = useState(false);
      return (
        <button type="button" data-testid="card-notes" onClick={() => setOpen(true)}>
          {open ? 'notes open' : 'notes closed'}
        </button>
      );
    }
    const thread = (items: ChatItem[]) => (
      <ChatThread
        state={ready(items)}
        specId="scatter-basic"
        language="python"
        onRequestTheme={vi.fn()}
        onFetchArtifact={vi.fn()}
        onTrack={vi.fn()}
        renderData={part => (part === 'data' ? <Card /> : null)}
      />
    );
    const before: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      { id: 2, kind: 'data' },
      { id: 3, kind: 'action', action: 'create_plot', library: 'matplotlib' },
      {
        id: 4,
        kind: 'plot_failed',
        result: {
          status: 'failed',
          reason: null,
          attempts: 2,
          artifacts: [],
          changes: [],
          residual_defects: [],
          version: null,
        },
      },
    ];
    const { rerender } = render(thread(before));
    const card = screen.getByTestId('card-notes');
    await userEvent.click(card);
    expect(card).toHaveTextContent('notes open');
    // `.undo()` after the plot: the stub stays where the card stood, the card goes on below the
    // plot as a new data chapter, the same node with the notes it had open.
    rerender(
      thread([
        before[0],
        { id: 5, kind: 'data_stub', rows: 2, columns: 2, card: 2 },
        before[2],
        before[3],
        { id: 2, kind: 'data' },
      ])
    );
    expect(screen.getByTestId('card-notes')).toBe(card);
    expect(card).toHaveTextContent('notes open');
    const log = screen.getByRole('log');
    expect([...log.children].map(child => child.textContent)).toEqual([
      '# data',
      '❯▤ table',
      'data · 2 rows × 2 cols',
      '# plot',
      '❯.create_plot()# matplotlib',
      'plot · failedno plot this time',
      '# data',
      'notes open',
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
      '# data',
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
    const older = screen.getByRole('button', { name: 'Plot v1, matplotlib, first plot' });
    expect(older).toHaveTextContent(/^▸plot v1 · matplotlib · first plot$/);
    expect(older).toHaveAttribute('aria-expanded', 'false');
    // The latest is open under its label, the request cut to 40 characters.
    const latest = screen.getByRole('button', {
      name: 'Plot v2, matplotlib, put the title in German and make the ma…',
    });
    expect(latest).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getAllByRole('img').map(image => image.getAttribute('alt'))).toEqual([
      'Adapted plot, version 2, light theme',
    ]);
  });

  it('labels a version that kept decisions by its request, the first plot as first plot, never kept 0', () => {
    const decided = (number: number, kept: string[]): PlotVersion => ({
      ...version(number),
      decisions: {
        kept: kept.map((text, index) => ({ id: `m${index + 1}`, text })),
        added: [],
      },
    });
    renderThread({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      versions: { 1: decided(1, []), 2: decided(2, ['title in German']), 3: version(3) },
      items: [
        { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' },
        { id: 2, kind: 'plot', version: 1 },
        { id: 3, kind: 'user', text: 'log scale on y' },
        { id: 4, kind: 'plot', version: 2 },
        { id: 5, kind: 'user', text: 'bigger markers' },
        { id: 6, kind: 'plot', version: 3 },
      ],
    });
    // What the version kept is the open card's line, never the label's: a folded version still
    // says what it answered, kept decisions or not, and whether the server named its memory.
    expect(screen.getByRole('button', { name: 'Plot v1, matplotlib, first plot' })).toBeVisible();
    expect(
      screen.getByRole('button', { name: 'Plot v2, matplotlib, log scale on y' })
    ).toHaveTextContent(/^▸plot v2 · matplotlib · log scale on y$/);
    expect(
      screen.getByRole('button', { name: 'Plot v3, matplotlib, bigger markers' })
    ).toBeVisible();
    expect(document.body).not.toHaveTextContent(/kept \d/);
  });
});

describe('ChatThread: questions and remembered decisions', () => {
  const ready = (items: ChatItem[], extra: Partial<AgentSessionState> = {}): AgentSessionState => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    items,
    ...extra,
  });
  const entry = (id: string, text: string) => ({
    id,
    kind: 'other',
    target: null,
    text,
    expect: null,
    turn: 2,
  });
  const MEMORY = {
    entries: [entry('m1', 'reference line at y = 7'), entry('m2', 'title in German')],
    max_entries: 30,
    written: true,
  };
  const log = () => screen.getByRole('log');
  /**
   * The log's text as its polite live region reads an addition: without what a screen reader
   * skips (`aria-hidden`) and without what is no live text in it (`aria-live="off"`).
   */
  const announced = () => {
    const copy = log().cloneNode(true) as HTMLElement;
    copy.querySelectorAll('[aria-hidden="true"], [aria-live="off"]').forEach(node => node.remove());
    return copy.textContent;
  };
  const thread = (
    state: AgentSessionState,
    decisions?: Parameters<typeof ChatThread>[0]['decisions']
  ) => (
    <ChatThread
      state={state}
      specId="scatter-basic"
      language="python"
      onRequestTheme={vi.fn()}
      onFetchArtifact={vi.fn()}
      onTrack={vi.fn()}
      decisions={decisions}
    />
  );
  const decisionsProps = () => ({
    disabled: false,
    onForget: vi.fn(async () => undefined),
    onForgetAll: vi.fn(async () => undefined),
    onAnnounce: vi.fn(),
  });

  it('marks a question once its turn settled, in the elements already there: the log reads the label once', () => {
    const asked: ChatItem = { id: 1, kind: 'user', text: 'what is on x?' };
    const reply: ChatItem = { id: 2, kind: 'assistant', text: 'The hours.' };
    const view = render(thread(ready([asked, reply])));
    const bubble = screen.getByText('what is on x?');
    const answer = screen.getByText('The hours.');
    const before = log().textContent ?? '';
    const heard = announced() ?? '';
    expect(screen.queryByTestId('question-mark')).not.toBeInTheDocument();

    // The `done` said `answer`, and the memory read after it is still to come: no mark yet.
    const marked: ChatItem = { ...asked, outcome: 'answer' };
    view.rerender(thread(ready([marked, reply], { memoryTurn: 1 })));
    expect(log().textContent).toBe(before);

    view.rerender(thread(ready([marked, reply], { memoryTurn: null })));
    expect(screen.getByText('what is on x?')).toBe(bubble);
    expect(screen.getByText('The hours.')).toBe(answer);
    expect(screen.getByTestId('question-mark')).toHaveAttribute('aria-hidden', 'true');
    expect(bubble).toHaveAttribute('id', 'agent-turn-1');
    expect(bubble).toHaveAttribute('tabindex', '-1');
    expect(bubble.textContent).toBe('Question: ❯what is on x?');
    expect(screen.getByTestId('answer-label').firstChild).toHaveTextContent(
      '? answer · nothing changed'
    );
    // What the polite log reads as it comes: the reply's label alone, once, in words.
    expect(announced()).toBe(heard.replace('The hours.', 'answer, nothing changedThe hours.'));
    // On screen also the chapter's count, the mark and, for a screen reader on the bubble, its word.
    expect(log().textContent).toBe(
      before
        .replace('# data', '# data·1 question')
        .replace('❯what', '?Question: ❯what')
        .replace('The hours.', '? answer · nothing changedanswer, nothing changedThe hours.')
    );
  });

  it('marks no note sent with a paste and no turn that changed something', () => {
    render(
      thread(
        ready([
          { id: 1, kind: 'paste', text: '▤ table' },
          { id: 2, kind: 'user', text: 'is share a fraction?', outcome: 'answer', note: true },
          { id: 3, kind: 'assistant', text: '12 rows; share is a fraction.' },
          { id: 4, kind: 'user', text: 'a title, ok?', outcome: 'kept' },
          { id: 5, kind: 'assistant', text: 'Kept for the first plot.' },
        ])
      )
    );
    expect(screen.queryByTestId('question-mark')).not.toBeInTheDocument();
    expect(screen.queryByTestId('answer-label')).not.toBeInTheDocument();
    expect(screen.queryByTestId('question-jump')).not.toBeInTheDocument();
  });

  it("jumps from a chapter's count to its questions in turn, back to the first after the last", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const items: ChatItem[] = [
        { id: 1, kind: 'paste', text: '▤ table' },
        { id: 2, kind: 'data' },
        { id: 3, kind: 'user', text: 'what is in b?', outcome: 'answer' },
        { id: 4, kind: 'assistant', text: 'Months.' },
        { id: 5, kind: 'user', text: 'and in c?', outcome: 'answer' },
        { id: 6, kind: 'assistant', text: 'Regions.' },
        { id: 7, kind: 'action', action: 'create_plot', library: 'matplotlib' },
        { id: 8, kind: 'user', text: 'why blue?', outcome: 'answer' },
        { id: 9, kind: 'assistant', text: 'The first colour.' },
      ];
      const view = render(thread(ready(items)));
      const lines = screen.getAllByTestId('chapter-line');
      expect(lines.map(line => line.textContent)).toEqual([
        '# data·2 questions',
        '# plot·1 question',
      ]);
      const data = within(lines[0]).getByRole('button', {
        name: '2 questions in this chapter, go to the next',
      });
      // The count stands beside the heading, never in it.
      expect(within(lines[0]).getByRole('heading', { level: 3 })).toHaveAccessibleName('data');
      const first = screen.getByText('what is in b?');
      const second = screen.getByText('and in c?');

      await user.click(data);
      expect(first).toHaveFocus();
      expect(first).toHaveAttribute('data-jump');
      await user.click(data);
      expect(second).toHaveFocus();
      await user.click(data);
      expect(first).toHaveFocus();
      // The highlight goes after a moment.
      vi.advanceTimersByTime(1600);
      expect(first).not.toHaveAttribute('data-jump');

      const plot = within(lines[1]).getByRole('button', {
        name: '1 question in this chapter, go to it',
      });
      await user.click(plot);
      expect(screen.getByText('why blue?')).toHaveFocus();

      // A question that comes in meanwhile: the next press goes on from the one it went to last.
      view.rerender(
        thread(
          ready([
            ...items,
            { id: 10, kind: 'user', text: 'and the dots?', outcome: 'answer' },
            { id: 11, kind: 'assistant', text: 'One per row.' },
          ])
        )
      );
      await user.click(plot);
      expect(screen.getByText('and the dots?')).toHaveFocus();
      await user.click(plot);
      expect(screen.getByText('why blue?')).toHaveFocus();
    } finally {
      vi.useRealTimers();
    }
  });

  it('puts the decisions on the latest plot line, and the list right after it, folded', async () => {
    const user = userEvent.setup();
    const items: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      { id: 2, kind: 'data' },
      { id: 3, kind: 'action', action: 'create_plot', library: 'matplotlib' },
      { id: 4, kind: 'assistant', text: 'Plot 1.' },
    ];
    render(thread(ready(items, { memory: MEMORY }), decisionsProps()));
    const [, plot] = screen.getAllByTestId('chapter-line');
    const toggle = within(plot).getByRole('button', { name: '2 decisions remembered' });
    expect(plot).toHaveTextContent('# plot·2 decisions ▾');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    const list = screen.getByTestId('plot-memory');
    expect(plot.nextElementSibling).toBe(list);
    expect(list).not.toBeVisible();
    // Unfolding adds no text to the log: the list was there, hidden, and is no live region.
    const before = log().textContent;
    await user.click(toggle);
    expect(list).toBeVisible();
    expect(list).toHaveAttribute('aria-live', 'off');
    expect(log().textContent).toBe(before?.replace('▾', '▴'));
  });

  it('shows no count while the memory is empty or unknown, and none without the page', () => {
    const items: ChatItem[] = [
      { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' },
    ];
    const view = render(thread(ready(items, { memory: null }), decisionsProps()));
    expect(screen.queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    view.rerender(
      thread(
        ready(items, { memory: { entries: [], max_entries: 30, written: true } }),
        decisionsProps()
      )
    );
    expect(log()).not.toHaveTextContent(/decision/);
    view.rerender(thread(ready(items, { memory: MEMORY })));
    expect(screen.queryByTestId('decisions-toggle')).not.toBeInTheDocument();
  });

  it('moves the list under a newer plot line with its node, its open state and a focus inside it', async () => {
    const user = userEvent.setup();
    const props = decisionsProps();
    const first: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      { id: 2, kind: 'data' },
      { id: 3, kind: 'action', action: 'create_plot', library: 'matplotlib' },
      { id: 4, kind: 'assistant', text: 'Plot 1.' },
    ];
    const view = render(thread(ready(first, { memory: MEMORY }), props));
    await user.click(screen.getByRole('button', { name: '2 decisions remembered' }));
    const list = screen.getByTestId('plot-memory');
    const forget = screen.getByRole('button', { name: 'Forget: title in German' });
    forget.focus();

    // A data change after the plot, then a plot of it: a `# data` and a newer `# plot` line.
    const later: ChatItem[] = [
      ...first,
      { id: 5, kind: 'user', text: 'only 2024', outcome: 'data' },
      { id: 6, kind: 'assistant', text: 'Kept 2024.' },
      { id: 7, kind: 'action', action: 'create_plot', library: 'matplotlib' },
    ];
    // A browser drops the focus of an element whose node moves, and React gives it back after the
    // commit: the DOM's insert drops it as a browser does, for this rerender.
    const insert = Node.prototype.insertBefore;
    Node.prototype.insertBefore = function <T extends Node>(
      this: Node,
      node: T,
      child: Node | null
    ) {
      const active = document.activeElement;
      if (active instanceof HTMLElement && node.contains(active)) active.blur();
      return insert.call(this, node, child) as T;
    };
    try {
      view.rerender(thread(ready(later, { memory: MEMORY }), props));
    } finally {
      Node.prototype.insertBefore = insert;
    }
    const lines = screen.getAllByTestId('chapter-line');
    expect(lines.map(line => line.dataset.chapter)).toEqual(['data', 'plot', 'data', 'plot']);
    expect(within(lines[1]).queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    expect(within(lines[3]).getByTestId('decisions-toggle')).toHaveAttribute(
      'aria-expanded',
      'true'
    );
    expect(screen.getByTestId('plot-memory')).toBe(list);
    expect(lines[3].nextElementSibling).toBe(list);
    expect(list).toBeVisible();
    expect(forget).toHaveFocus();
  });

  it('holds the decisions on the new data line after a paste with other columns, with .forget_all()', async () => {
    // Owner decision of 2026-11-08: the decisions of the earlier plot stand where the user looks
    // before the next plot takes them over; one click forgets them all, and ignoring keeps them.
    const user = userEvent.setup();
    const props = decisionsProps();
    const snapshot: DataSnapshot = {
      n: 2,
      change: 'paste',
      summary: 'pasted',
      label: 'data v2 · pasted',
      rows: 3,
      columns: 2,
      sheet: null,
      fileName: null,
      changes: [],
      preview: [['0.25', '1.003']],
      profile: {
        rows: 3,
        columns: [
          { name: 'Length (m)', dtype: 'number', missing: 0, unique: 3 },
          { name: 'Period (s)', dtype: 'number', missing: 0, unique: 3 },
        ],
        source_format: 'csv',
        decimal: '.',
        warnings: [],
      },
      columnsChanged: true,
    };
    const items: ChatItem[] = [
      { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' },
      { id: 2, kind: 'assistant', text: 'Plot 1.' },
      { id: 3, kind: 'paste', text: '▤ pendulum' },
      { id: 4, kind: 'data', snapshot },
    ];
    render(thread(ready(items, { memory: MEMORY }), props));

    const lines = screen.getAllByTestId('chapter-line');
    expect(lines.map(line => line.dataset.chapter)).toEqual(['plot', 'data']);
    expect(within(lines[0]).queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    expect(lines[1]).toHaveTextContent('# data·2 earlier decisions ▾·.forget_all()');
    expect(screen.getByTestId('plot-memory')).not.toBeVisible();

    await user.click(
      within(lines[1]).getByRole('button', { name: 'Forget all earlier decisions' })
    );
    expect(props.onForgetAll).toHaveBeenCalledTimes(1);
    expect(props.onAnnounce).toHaveBeenCalledWith('forgot every decision');
    // The list opened for it: its progress and a failure show there.
    expect(screen.getByTestId('plot-memory')).toBeVisible();
  });

  it('announces a removal through the page, outside the log, which loses the entry and gains nothing', async () => {
    const user = userEvent.setup();
    const props = decisionsProps();
    const items: ChatItem[] = [
      { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' },
      { id: 2, kind: 'assistant', text: 'Plot 1.' },
    ];
    const view = render(thread(ready(items, { memory: MEMORY }), props));
    await user.click(screen.getByRole('button', { name: '2 decisions remembered' }));
    await user.click(screen.getByRole('button', { name: 'Forget: title in German' }));
    expect(props.onForget).toHaveBeenCalledWith('m2');
    expect(props.onAnnounce).toHaveBeenCalledWith('forgot: title in German');
    const before = log().textContent ?? '';
    view.rerender(
      thread(ready(items, { memory: { ...MEMORY, entries: MEMORY.entries.slice(0, 1) } }), props)
    );
    const after = log().textContent ?? '';
    expect(after).toBe(
      before.replace('title in German.forget()', '').replace('2 decisions', '1 decision')
    );
  });
});
