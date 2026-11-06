import { describe, expect, it } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import {
  pendingReply,
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

  it('names .stop() in the status line while a plot runs, and that it stops once pressed', () => {
    expect(runLine(running(queued('create_plot')))).toBe('plotting… .stop() to cancel');
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
    expect(stepOneLine(step1())).toBe(
      'check the preview and the bindings above, then .create_plot()'
    );
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

  it('leads to .plot_all() while all is pressed, where no .create_plot() shows', () => {
    expect(stepOneLine(step1(), '.plot_all()')).toBe(
      'check the preview and the bindings above, then .plot_all()'
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
    carryText: null,
    chatLocked: false,
  };
  const plotted = {
    1: { version: 1, library: 'matplotlib' },
  } as unknown as AgentSessionState['versions'];

  it('names step 1 and its data without data, and what to check with it', () => {
    expect(statusLine(ready(), options)).toEqual({ step: 1, text: 'step 1 of 2 · your data' });
    expect(statusLine(ready({ dataset }), options)).toEqual({
      step: 1,
      text: 'step 1 of 2 · check the preview and the bindings above, then .create_plot()',
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
      text: 'step 2 of 2 · plotting… .stop() to cancel',
    });
    expect(
      statusLine(confirmed, { ...options, attachmentLine: 'the attached table is read' }).text
    ).toBe('step 2 of 2 · the attached table is read');
  });

  it("says in step 2 what the plot button does before the library's first plot, then the data", () => {
    const confirmed = ready({ dataset, dataConfirmed: true });
    expect(statusLine(confirmed, options).text).toBe(
      'step 2 of 2 · create the plot as it is, or say first what it should do differently'
    );
    expect(
      statusLine(confirmed, { ...options, carryText: 'plot in seaborn with your 2 decisions' }).text
    ).toBe(
      'step 2 of 2 · plot in seaborn with your 2 decisions, or say first what it should do differently'
    );
    // While `all` holds the box, the composer's own line says why; the status line names the data.
    expect(statusLine(confirmed, { ...options, chatLocked: true }).text).toBe(
      'step 2 of 2 · data fits · 2 rows · 0 columns · version 3'
    );
    expect(statusLine({ ...confirmed, versions: plotted }, options).text).toBe(
      'step 2 of 2 · data fits · 2 rows · 0 columns · version 3'
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
