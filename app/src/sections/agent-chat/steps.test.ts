import { describe, expect, it } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import {
  pendingReply,
  runLine,
  runView,
  showsTimeline,
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

  it('names .stop() above the composer while a plot runs, and that it stops once pressed', () => {
    expect(runLine(running(queued('create_plot')))).toBe('# plotting… .stop() to cancel');
    expect(runLine(running({ ...queued('carry_plot'), stopping: true }))).toBe('# stopping…');
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

  it('names what .create_plot() waits for, and after a loss says step 1 again', () => {
    expect(stepOneLine(step1())).toBe(
      '# step 1 — check the preview and the bindings above, then .create_plot()'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'] }))).toBe(
      '# step 1 — pick a column for y, then .create_plot()'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'], confirmLoss: 'bindings' }))).toBe(
      '# step 1 again — pick a column for y, then .create_plot()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'data' }))).toBe(
      '# step 1 again — the data changed · check it above, then .create_plot()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'bindings' }))).toBe(
      '# step 1 again — bindings changed · check them above, then .create_plot()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'server' }))).toBe(
      '# step 1 again — not confirmed on the server · check the data, then .create_plot()'
    );
  });

  it('leads to .plot_all() while all is pressed, where no .create_plot() shows', () => {
    expect(stepOneLine(step1(), '.plot_all()')).toBe(
      '# step 1 — check the preview and the bindings above, then .plot_all()'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'] }), '.plot_all()')).toBe(
      '# step 1 — pick a column for y, then .plot_all()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'data' }), '.plot_all()')).toBe(
      '# step 1 again — the data changed · check it above, then .plot_all()'
    );
  });
});
