import { describe, expect, it } from 'vitest';

import {
  type AgentSessionState,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import {
  pendingReply,
  plotButtonLabel,
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
    // After a data change the plot button reads `plot the new data`, and the line ends with it.
    expect(stepOneLine(step1({ confirmLoss: 'data' }))).toBe(
      '# step 1 again — data changed · check it above, then plot the new data'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'], confirmLoss: 'data' }))).toBe(
      '# step 1 again — pick a column for y, then plot the new data'
    );
    expect(stepOneLine(step1({ confirmLoss: 'bindings' }))).toBe(
      '# step 1 again — bindings changed · check them above, then .create_plot()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'server' }))).toBe(
      '# step 1 again — check the data above, then .create_plot()'
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
      '# step 1 — check the preview and the bindings above, then .plot_all()'
    );
    expect(stepOneLine(step1({ missingRoles: ['y'] }), '.plot_all()')).toBe(
      '# step 1 — pick a column for y, then .plot_all()'
    );
    expect(stepOneLine(step1({ confirmLoss: 'data' }), '.plot_all()')).toBe(
      '# step 1 again — data changed · check it above, then .plot_all()'
    );
  });
});
