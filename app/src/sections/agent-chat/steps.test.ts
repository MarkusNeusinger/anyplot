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
  runLine,
  runView,
  showsTimeline,
  statusLine,
  stepAnnouncement,
  stepOneLine,
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

describe('the waits of a turn', () => {
  it('gives a queued example_data turn one indicator: the in-progress line, no timeline', () => {
    const state = running(queued('example_data'));
    expect(pendingReply(state)).toBe('example_data');
    expect(showsTimeline(state)).toBe(false);
  });

  it('keeps the timeline for a queued plot run and for any turn that reached a pipeline step', () => {
    expect(showsTimeline(running(queued('create_plot')))).toBe(true);
    const stepped = running({
      ...queued('message'),
      steps: [
        { step: 'queued', attempt: null },
        { step: 'adapting', attempt: 1 },
      ],
      queue: null,
    });
    expect(showsTimeline(stepped)).toBe(true);
    expect(pendingReply(stepped)).toBeNull();
  });

  it('says in the status line that a plot runs and how long it takes, and that it stops once pressed', () => {
    // `.stop()` stands at the line's end as a button of its own, so the words leave it out.
    expect(runLine(running(queued('create_plot')))).toBe('drawing your plot · usually 1–3 min');
    expect(runLine(running({ ...queued('carry_plot'), stopping: true }))).toBe('stopping…');
    // A turn without a pipeline step keeps the step's line: its in-progress line says what runs.
    expect(runLine(running(queued('example_data')))).toBeNull();
    expect(runLine({ ...initialAgentState('matplotlib'), phase: 'ready' })).toBeNull();
    // The run's card took the timeline's place while the reply is still on its way: no plotting.
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

  it('holds what a run sends into the thread while its timeline stands below it', () => {
    // Above the timeline it pushed the timeline and the composer down mid-run.
    const state = { ...running(plotRun), items: [ask, note] };
    expect(runView(state)).toEqual({ items: [ask], timeline: true });
  });

  it('never holds a data version back: the live card would unmount', () => {
    // A version under a running timeline (none arrives there today) keeps the card in the
    // thread, and the stub it left; only the talk waits.
    const stub = { id: 4, kind: 'data_stub', rows: 2, columns: 2, card: 5 } as const;
    const live = { id: 5, kind: 'data' } as const;
    const state = { ...running(plotRun), items: [ask, note, stub, live] };
    expect(runView(state)).toEqual({ items: [ask, stub, live], timeline: true });
  });

  it("lets the run's result card take the timeline's place, with the held items", () => {
    const card = { id: 3, kind: 'plot', version: 1 } as const;
    const state = { ...running(plotRun), items: [ask, note, card] };
    expect(runView(state)).toEqual({ items: [ask, note, card], timeline: false });
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
      timeline: false,
    });
  });

  it('holds nothing for a turn without the timeline, nor once the run is over', () => {
    const question = running(queued('message'));
    expect(runView({ ...question, items: [ask, note] }).items).toEqual([ask, note]);
    expect(runView({ ...running(plotRun), run: null, items: [ask, note] })).toEqual({
      items: [ask, note],
      timeline: false,
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
    expect(statusLine(ready(), options)).toEqual({ step: 1, text: 'step 1 of 2 · your data' });
    expect(statusLine(ready({ dataset }), options)).toEqual({
      step: 1,
      text: 'step 1 of 2 · check the data and the bindings above, then .create_plot()',
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
    expect(statusLine(ready({ transcription }), options)).toEqual({
      step: 1,
      text: 'step 1 of 2 · decide on the table first: .use() or .discard()',
    });
  });

  it('says back to step 1 after a lost confirmation, with what lost it', () => {
    expect(statusLine(ready({ dataset, confirmLoss: 'bindings' }), options).text).toBe(
      'back to step 1 of 2 · bindings changed · check them above, then .create_plot()'
    );
  });

  it("puts a waiting attachment first, then a plot's run, before the step's own words", () => {
    const run = queued('create_plot');
    const confirmed = ready({ dataset, dataConfirmed: true, run, items: running(run).items });
    expect(statusLine(confirmed, options)).toEqual({
      step: 2,
      text: 'step 2 of 2 · drawing your plot · usually 1–3 min',
    });
    expect(
      statusLine(confirmed, { ...options, attachmentLine: 'the attached table is read' }).text
    ).toBe('step 2 of 2 · the attached table is read');
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
