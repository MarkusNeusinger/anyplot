import { describe, expect, it } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  type DataSnapshot,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import {
  pendingReply,
  plotButtonKind,
  plotButtonLabel,
  plotWork,
  runLine,
  runView,
  statusLine,
  stepAnnouncement,
  stepOneLine,
  trySegment,
  workingLine,
} from 'src/sections/agent-chat/steps';

const queued = (kind: RunState['kind']): RunState => ({
  kind,
  steps: [{ step: 'queued', attempt: null }],
  queue: { position: 1, waiting: 2 },
  stopping: false,
});

/** A session in the middle of a turn of `kind`, its own prompt the thread's last item. */
function running(run: RunState): AgentSessionState {
  return {
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    items: [{ id: 1, kind: 'action', action: 'example_data', library: 'matplotlib' }],
    run,
  };
}

/** A plot run that started at `T0` and reached `steps`, the attempt of each. */
const T0 = 1_000_000;
const drawing = (steps: [string, number][], extra: Partial<RunState> = {}): RunState => ({
  kind: 'create_plot',
  steps: steps.map(([step, attempt]) => ({ step: step as RunState['steps'][0]['step'], attempt })),
  queue: null,
  stopping: false,
  startedAt: T0,
  ...extra,
});

/** The working line as the eye reads it: its words, and `· clock` where a clock follows them. */
const line = (state: AgentSessionState) => {
  const working = workingLine(state);
  return working && { text: working.text, short: working.short, clock: working.clockFrom };
};

describe('the working line', () => {
  it('gives a queued example_data turn one line that says where it waits, and no plot work', () => {
    const state = running(queued('example_data'));
    expect(pendingReply(state)).toBe('example_data');
    expect(plotWork(state)).toBe(false);
    // Owner, 2026-11-09 (open point 1, option a): the position in the line in view, never a clock.
    expect(line(state)).toEqual({
      text: 'waiting · you are next',
      short: 'waiting · you are next',
      clock: null,
    });
    expect(line(running({ ...queued('message'), queue: { position: 3, waiting: 5 } }))?.text).toBe(
      'waiting · you are 3rd'
    );
    expect(line(running({ ...queued('message'), queue: null }))?.text).toBe('waiting');
  });

  it('keeps the words of a turn without plot work, and no clock', () => {
    const started = (kind: RunState['kind']) =>
      running({ kind, steps: [], queue: null, stopping: false, startedAt: T0 });
    expect(line(started('summarize_data'))).toEqual({
      text: 'summarizing your data',
      short: 'summarizing your data',
      clock: null,
    });
    expect(line(started('example_data'))?.text).toBe('making example data');
    expect(line(started('message'))?.text).toBe('working on your message');
    // Its first reply takes the line's place.
    const replied = started('message');
    expect(
      line({ ...replied, items: [...replied.items, { id: 2, kind: 'assistant', text: 'Hi.' }] })
    ).toBeNull();
    expect(line({ ...replied, run: null })).toBeNull();
  });

  it('draws a plot run and any turn that reached a pipeline step, with the clock from its start', () => {
    expect(plotWork(running(queued('create_plot')))).toBe(true);
    // A plot run waiting in the queue: its position, no clock yet.
    expect(line(running(queued('create_plot')))).toEqual({
      text: 'waiting · you are next',
      short: 'waiting · you are next',
      clock: null,
    });
    // Before its first step and through the first try: no try segment (owner, 2026-11-09).
    for (const steps of [[], [['adapting', 1]], [['reviewing', 1]]] as [string, number][][]) {
      expect(line(running(drawing(steps)))).toEqual({
        text: 'drawing your plot',
        short: 'drawing',
        clock: T0,
      });
    }
    const stepped = running({
      ...queued('message'),
      steps: [
        { step: 'queued', attempt: null },
        { step: 'adapting', attempt: 1 },
      ],
      queue: null,
      startedAt: T0,
    });
    expect(plotWork(stepped)).toBe(true);
    expect(pendingReply(stepped)).toBeNull();
    expect(line(stepped)?.text).toBe('drawing your plot');
    // The late read of a cut turn was not timed: no clock, never a wrong time.
    expect(line(running(drawing([['adapting', 1]], { startedAt: undefined })))?.clock).toBeNull();
  });

  it('names the try from the second on: by the server cap, else in words', () => {
    const second: [string, number][] = [
      ['reviewing', 1],
      ['repairing', 2],
    ];
    expect(line(running(drawing(second)))).toEqual({
      text: 'drawing your plot · second try',
      short: 'drawing · second try',
      clock: T0,
    });
    expect(line(running(drawing(second, { maxAttempts: 2 })))?.text).toBe(
      'drawing your plot · try 2 of 2'
    );
    expect(line(running(drawing(second, { maxAttempts: 3 })))?.short).toBe('drawing · try 2 of 3');
    // The first try stays short, also with the cap; a cap is never a constant of the page.
    expect(line(running(drawing([['adapting', 1]], { maxAttempts: 2 })))?.text).toBe(
      'drawing your plot'
    );
    expect(trySegment(drawing([['repairing', 3]]))).toBe('third try');
    expect(trySegment(drawing([['repairing', 3]], { maxAttempts: 2 }))).toBe('try 3 of 3');
  });

  it('says the stop, the reconnect and the reply after the card, without a clock', () => {
    const steps: [string, number][] = [['rendering', 1]];
    expect(line(running(drawing(steps, { stopping: true })))?.text).toBe(
      'stopping after this step…'
    );
    expect(line(running(drawing([], { stopping: true })))?.text).toBe('stopping…');
    expect(line(running({ ...queued('create_plot'), stopping: true }))?.text).toBe(
      'leaving the queue…'
    );
    expect(line(running({ ...queued('message'), stopping: true }))?.text).toBe(
      'leaving the queue…'
    );
    expect(line(running(drawing(steps, { reconnecting: true })))).toEqual({
      text: 'connection lost · reconnecting…',
      short: 'connection lost · reconnecting…',
      clock: null,
    });
    const card = running(drawing(steps));
    const withCard = {
      ...card,
      items: [...card.items, { id: 2, kind: 'plot' as const, version: 1 }],
    };
    expect(line(withCard)).toEqual({
      text: 'writing the reply',
      short: 'writing the reply',
      clock: null,
    });
  });

  it('gives its place to an error or a refusal that ended the turn', () => {
    const state = running(drawing([['adapting', 1]]));
    const error = { id: 2, kind: 'error', code: 'no_reply', ref: 'r-1' } as const;
    expect(runView({ ...state, items: [...state.items, error] }).drawing).toBe(false);
    expect(line({ ...state, items: [...state.items, error] })).toBeNull();
    const refusal = { id: 2, kind: 'refusal', code: 'service_paused', text: 'paused' } as const;
    expect(line({ ...state, items: [...state.items, refusal] })).toBeNull();
    // The same for a turn without plot work, whose prompt is no longer the last item.
    const question = running({ kind: 'message', steps: [], queue: null, stopping: false });
    expect(line({ ...question, items: [...question.items, error] })).toBeNull();
  });

  it('says in the status line that a plot is drawn, its clock apart, and that it stops once pressed', () => {
    // `.stop()` stands at the line's end as a button of its own, so the words leave it out.
    expect(runLine(running(drawing([['adapting', 1]])))).toEqual({
      words: 'drawing your plot',
      short: 'drawing',
      clockFrom: T0,
      tail: 'usually 1–3 min',
    });
    // While the run waits in the queue the clock does not run.
    expect(runLine(running(queued('create_plot')))?.clockFrom).toBeNull();
    expect(runLine(running({ ...queued('carry_plot'), stopping: true }))).toEqual({
      words: 'stopping…',
      short: 'stopping…',
      clockFrom: null,
      tail: '',
    });
    // A turn without a pipeline step keeps the step's line: its working line says what runs.
    expect(runLine(running(queued('example_data')))).toBeNull();
    expect(runLine({ ...initialAgentState('matplotlib'), phase: 'ready' })).toBeNull();
    // The run's card is in while the reply is still on its way: no drawing.
    const shipped = running(queued('create_plot'));
    expect(
      runLine({ ...shipped, items: [...shipped.items, { id: 2, kind: 'plot', version: 1 }] })
    ).toBeNull();
  });
});

describe('runView', () => {
  const plotRun: RunState = {
    kind: 'create_plot',
    steps: [{ step: 'adapting', attempt: 1 }],
    queue: null,
    stopping: false,
  };
  const ask = { id: 1, kind: 'action', action: 'create_plot', library: 'matplotlib' } as const;
  const note = { id: 2, kind: 'assistant', text: 'Adapting the catalogue plot.' } as const;

  it('holds what a run sends into the thread while a plot is drawn', () => {
    // Above the working line it pushed the line and the composer down mid-run.
    const state = { ...running(plotRun), items: [ask, note] };
    expect(runView(state)).toEqual({ items: [ask], drawing: true });
  });

  it('never holds a data version back: the live card would unmount', () => {
    // A version while a plot is drawn (none arrives there today) keeps the card in the thread,
    // and the stub it left; only the talk waits.
    const stub = { id: 4, kind: 'data_stub', rows: 2, columns: 2, card: 5 } as const;
    const live = { id: 5, kind: 'data' } as const;
    const state = { ...running(plotRun), items: [ask, note, stub, live] };
    expect(runView(state)).toEqual({ items: [ask, stub, live], drawing: true });
  });

  it("lets the run's result card end the drawing, with the held items", () => {
    const card = { id: 3, kind: 'plot', version: 1 } as const;
    const state = { ...running(plotRun), items: [ask, note, card] };
    expect(runView(state)).toEqual({ items: [ask, note, card], drawing: false });
    // A run that failed hands over to its card the same way.
    const failed = {
      id: 3,
      kind: 'plot_failed',
      result: {
        status: 'failed',
        reason: 'render_failed',
        attempts: 2,
        artifacts: [],
        changes: [],
      },
    } as unknown as Extract<ChatItem, { kind: 'plot_failed' }>;
    expect(runView({ ...running(plotRun), items: [ask, note, failed] })).toEqual({
      items: [ask, note, failed],
      drawing: false,
    });
  });

  it('holds nothing for a turn without plot work, nor once the run is over', () => {
    const question = running(queued('message'));
    expect(runView({ ...question, items: [ask, note] }).items).toEqual([ask, note]);
    expect(runView({ ...running(plotRun), run: null, items: [ask, note] })).toEqual({
      items: [ask, note],
      drawing: false,
    });
  });
});

describe('stepOneLine', () => {
  const dataset = {
    bytes: 10,
    parsed: {
      preview: [],
      profile: { rows: 1, columns: [], source_format: 'csv', decimal: '.', warnings: [] },
      bindings: [],
      warnings: [],
      version: 1,
    },
  };
  const step1 = (overrides: Partial<AgentSessionState> = {}): AgentSessionState => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    dataset,
    ...overrides,
  });

  it('names nothing without data or in step 2', () => {
    expect(stepOneLine(step1({ dataset: null }))).toBeNull();
    expect(stepOneLine(step1({ dataConfirmed: true }))).toBeNull();
  });

  it('names what .create_plot() waits for, and after a loss what lost it', () => {
    // The data, not the preview: a phone's card shows no preview table, and the line is the same
    // at every width.
    expect(stepOneLine(step1())).toBe('check the data and the bindings above, then .create_plot()');
    expect(stepOneLine(step1({ missingRoles: ['y'] }))).toBe(
      'pick a column for y, then .create_plot()'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'], confirmLoss: 'bindings' }))).toBe(
      'pick a column for y, then .create_plot()'
    );
    // After a data change the plot button reads `plot the new data`, and the line ends with it.
    expect(stepOneLine(step1({ confirmLoss: 'data' }))).toBe(
      'data changed · check it above, then plot the new data'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'], confirmLoss: 'data' }))).toBe(
      'pick a column for y, then plot the new data'
    );
    expect(stepOneLine(step1({ confirmLoss: 'bindings' }))).toBe(
      'bindings changed · check them above, then .create_plot()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'server' }))).toBe(
      'check the data above, then .create_plot()'
    );
  });

  it('names the plot button after the data the user had confirmed changed', () => {
    expect(plotButtonLabel(step1())).toBe('.create_plot()');
    expect(plotButtonLabel(step1({ confirmLoss: 'bindings' }))).toBe('.create_plot()');
    expect(plotButtonLabel(step1({ confirmLoss: 'server' }))).toBe('.create_plot()');
    expect(plotButtonLabel(step1({ confirmLoss: 'data' }))).toBe('plot the new data');
  });

  it('names the plot button .update_plot() once the library has a plot, in its own library only', () => {
    const plotted = {
      1: { version: 1, library: 'matplotlib' },
    } as unknown as AgentSessionState['versions'];
    expect(plotButtonKind(step1({ dataConfirmed: true, versions: plotted }))).toBe('update');
    expect(plotButtonLabel(step1({ dataConfirmed: true, versions: plotted }))).toBe(
      '.update_plot()'
    );
    // Bindings changed after the plot: the button keeps its name, and the step line leads to it.
    expect(stepOneLine(step1({ versions: plotted, confirmLoss: 'bindings' }))).toBe(
      'bindings changed · check them above, then .update_plot()'
    );
    // New data says so, with or without a plot, also a paste after the plot, which clears the
    // loss's reason; a switch to a library without a plot creates it.
    expect(plotButtonKind(step1({ versions: plotted, confirmLoss: 'data' }))).toBe('new_data');
    expect(plotButtonKind(step1({ versions: plotted }))).toBe('new_data');
    expect(plotButtonKind(step1({ versions: plotted, library: 'seaborn' }))).toBe('create');
    expect(plotButtonKind(step1({ versions: plotted }), true)).toBe('all');
  });

  it('names the plot the click makes of new data in the box: the first plot, or the new data', () => {
    const plotted = {
      1: { version: 1, library: 'matplotlib' },
    } as unknown as AgentSessionState['versions'];
    expect(plotButtonKind(step1({ dataset: null }), false, true)).toBe('create');
    // On a current plot the button would update it; with data in the box it plots that data.
    const current = step1({ dataConfirmed: true, versions: plotted });
    expect(plotButtonKind(current)).toBe('update');
    expect(plotButtonKind(current, false, true)).toBe('new_data');
    expect(plotButtonLabel(current, true)).toBe('plot the new data');
    expect(plotButtonKind(current, true, true)).toBe('all');
    expect(plotButtonKind(step1({ versions: plotted, library: 'seaborn' }), false, true)).toBe(
      'create'
    );
  });

  it('leads to .plot_all() while all is pressed, where no .create_plot() shows', () => {
    expect(stepOneLine(step1(), '.plot_all()')).toBe(
      'check the data and the bindings above, then .plot_all()'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'] }), '.plot_all()')).toBe(
      'pick a column for y, then .plot_all()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'data' }), '.plot_all()')).toBe(
      'data changed · check it above, then .plot_all()'
    );
  });
});

describe('statusLine', () => {
  const dataset = {
    bytes: 10,
    parsed: {
      preview: [],
      profile: { rows: 2, columns: [], source_format: 'csv', decimal: '.', warnings: [] },
      bindings: [],
      warnings: [],
      version: 3,
    },
  };
  const ready = (overrides: Partial<AgentSessionState> = {}): AgentSessionState => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    ...overrides,
  });
  const options = {
    action: '.create_plot()',
    attachmentLine: null,
    carry: null,
    lockedLibraries: null,
  };
  const plotted = {
    1: { version: 1, library: 'matplotlib' },
  } as unknown as AgentSessionState['versions'];

  it('names step 1 and its data without data, and what to check with it', () => {
    expect(statusLine(ready(), options)).toEqual({
      step: 1,
      head: 'step 1 of 2',
      text: 'step 1 of 2 · your data',
      run: null,
    });
    expect(statusLine(ready({ dataset }), options)).toEqual({
      step: 1,
      head: 'step 1 of 2',
      text: 'step 1 of 2 · check the data and the bindings above, then .create_plot()',
      run: null,
    });
  });

  it('asks for the decision on a table read from text before any data was stored', () => {
    const transcription = {
      text: 'a,b\n1,2\n',
      preview: [['1', '2']],
      profile: dataset.parsed.profile,
      warnings: [],
      note: '',
      bytes: 8,
    };
    expect(statusLine(ready({ transcription }), options).text).toBe(
      'step 1 of 2 · decide on the table first: .use() or .discard()'
    );
  });

  it('says back to step 1 after a lost confirmation, with what lost it', () => {
    expect(statusLine(ready({ dataset, confirmLoss: 'bindings' }), options).text).toBe(
      'back to step 1 of 2 · bindings changed · check them above, then .create_plot()'
    );
  });

  it("puts a waiting attachment first, then a plot's run, before the step's own words", () => {
    const run: RunState = { ...queued('create_plot'), steps: [], queue: null, startedAt: 5 };
    const confirmed = ready({ dataset, dataConfirmed: true, run, items: running(run).items });
    // The description reads no clock; the line shows it between the words and the usual time.
    expect(statusLine(confirmed, options)).toEqual({
      step: 2,
      head: 'step 2 of 2',
      text: 'step 2 of 2 · drawing your plot · usually 1–3 min',
      run: { words: 'drawing your plot', short: 'drawing', clockFrom: 5, tail: 'usually 1–3 min' },
    });
    expect(
      statusLine(confirmed, { ...options, attachmentLine: 'the attached table is read' })
    ).toMatchObject({ text: 'step 2 of 2 · the attached table is read', run: null });
    expect(statusLine({ ...confirmed, run: { ...run, stopping: true } }, options).text).toBe(
      'step 2 of 2 · stopping…'
    );
  });

  it("puts the one click's reading before everything, and where it stopped in step 1's place", () => {
    const readingLine = 'reading your data';
    const stopLine = 'the assistant asked a question · answer it in the box, or .create_plot()';
    expect(
      statusLine(ready({ dataset }), { ...options, readingLine, attachmentLine: 'attached' }).text
    ).toBe('step 1 of 2 · reading your data');
    expect(statusLine(ready({ dataset }), { ...options, stopLine }).text).toBe(
      `step 1 of 2 · ${stopLine}`
    );
    // A new attachment and a plot that runs come first; in step 2 the stop is over.
    expect(
      statusLine(ready({ dataset }), { ...options, stopLine, attachmentLine: 'attached' }).text
    ).toBe('step 1 of 2 · attached');
    const run = queued('create_plot');
    expect(
      statusLine(ready({ dataset, run, items: running(run).items }), { ...options, stopLine }).text
    ).toBe('step 1 of 2 · drawing your plot · usually 1–3 min');
    expect(statusLine(ready({ dataset, dataConfirmed: true }), { ...options, stopLine }).text).toBe(
      'step 2 of 2 · create the plot as it is, or say first what it should do differently'
    );
  });

  it("says in step 2 what the plot button does before the library's first plot, then the data", () => {
    const confirmed = ready({ dataset, dataConfirmed: true });
    expect(statusLine(confirmed, options).text).toBe(
      'step 2 of 2 · create the plot as it is, or say first what it should do differently'
    );
    // After a switch the plot button keeps its name: the line names the decisions it keeps.
    const carry = { library: 'seaborn', decisions: 2 };
    expect(statusLine(confirmed, { ...options, carry }).text).toBe(
      'step 2 of 2 · 2 decisions kept in seaborn · create the plot as it is, or say first what it should do differently'
    );
    expect(statusLine(confirmed, { ...options, carry: { ...carry, decisions: 0 } }).text).toBe(
      'step 2 of 2 · create the plot as it is, or say first what it should do differently'
    );
    expect(
      statusLine(
        { ...confirmed, versions: plotted },
        { ...options, action: '.update_plot()', carry }
      ).text
    ).toBe(
      'step 2 of 2 · 2 decisions kept in seaborn · .update_plot() brings them in, or ask for a change'
    );
    // While `all` holds the box, the line says what `.plot_all()` does and how to chat again.
    expect(statusLine(confirmed, { ...options, lockedLibraries: 15 }).text).toBe(
      'step 2 of 2 · plot the table as it is in all 15 libraries at once · turn all off to chat'
    );
    // The confirmed data by the number its card carries (`data v3`), never the server's version,
    // which starts over with every paste; a thread built without snapshots names no number.
    expect(statusLine({ ...confirmed, versions: plotted }, options).text).toBe(
      'step 2 of 2 · data fits · 2 rows · 0 columns'
    );
    const card = { id: 7, kind: 'data' as const, snapshot: { n: 3 } as DataSnapshot };
    expect(statusLine({ ...confirmed, versions: plotted, items: [card] }, options).text).toBe(
      'step 2 of 2 · data v3 fits · 2 rows · 0 columns'
    );
  });

  it('announces the step and a parse in the hidden region, nothing before data', () => {
    expect(stepAnnouncement(ready())).toBe('');
    expect(stepAnnouncement(ready({ parsing: true }))).toBe('parsing your data');
    expect(stepAnnouncement(ready({ dataset }))).toBe(
      'step 1: check the data, then create the plot'
    );
    expect(stepAnnouncement(ready({ dataset, dataConfirmed: true }))).toBe(
      'step 2: the data is confirmed; create the plot below'
    );
  });
});
