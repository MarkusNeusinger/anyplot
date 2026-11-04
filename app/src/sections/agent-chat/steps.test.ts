import { describe, expect, it } from 'vitest';

import {
  type AgentSessionState,
  initialAgentState,
  type RunState,
} from 'src/hooks/useAgentSession';
import { confirmStepLine, pendingReply, showsTimeline } from 'src/sections/agent-chat/steps';

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

describe('confirmStepLine', () => {
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
    expect(confirmStepLine(step1({ dataset: null }))).toBeNull();
    expect(confirmStepLine(step1({ dataConfirmed: true }))).toBeNull();
  });

  it('names what the confirmation waits for, and after a loss says step 1 again', () => {
    expect(confirmStepLine(step1())).toBe(
      '# step 1 — check the preview and the bindings, then confirm'
    );
    expect(confirmStepLine(step1({ missingRoles: ['y'] }))).toBe(
      '# step 1 — pick a column for y, then confirm'
    );
    expect(confirmStepLine(step1({ missingRoles: ['y'], confirmLoss: 'bindings' }))).toBe(
      '# step 1 again — pick a column for y, then confirm'
    );
    expect(confirmStepLine(step1({ confirmLoss: 'data' }))).toBe(
      '# step 1 again — the data changed · confirm it again'
    );
  });
});
