import { describe, expect, it } from 'vitest';

import { type AgentSessionState, initialAgentState } from 'src/hooks/useAgentSession';
import type { PlotResult } from 'src/lib/agent';
import { type FanOutSlot, grantSlots, runStatus } from 'src/sections/agent-chat/fanoutRules';

const ORDER = ['matplotlib', 'seaborn', 'plotnine', 'altair'];

describe('grantSlots', () => {
  it('starts the waiting libraries in the page order up to the limit', () => {
    const slots: Record<string, FanOutSlot> = {
      matplotlib: 'waiting',
      seaborn: 'data',
      plotnine: 'waiting',
      altair: 'waiting',
    };
    expect(grantSlots(slots, ORDER, 2)).toEqual({
      matplotlib: 'running',
      seaborn: 'data',
      plotnine: 'running',
      altair: 'waiting',
    });
  });

  it('counts the running libraries and starts the next once one is done', () => {
    const full: Record<string, FanOutSlot> = {
      matplotlib: 'running',
      seaborn: 'running',
      plotnine: 'waiting',
      altair: 'waiting',
    };
    expect(grantSlots(full, ORDER, 2)).toEqual(full);
    expect(grantSlots({ ...full, seaborn: 'done' }, ORDER, 2)).toEqual({
      matplotlib: 'running',
      seaborn: 'done',
      plotnine: 'running',
      altair: 'waiting',
    });
  });
});

const ready = (patch: Partial<AgentSessionState> = {}): AgentSessionState => ({
  ...initialAgentState('seaborn'),
  phase: 'ready',
  sessionId: 'S1',
  ...patch,
});

const result = (patch: Partial<PlotResult> = {}): PlotResult =>
  ({
    status: 'ok',
    reason: null,
    attempts: 1,
    artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
    changes: [],
    residual_defects: [],
    version: 1,
    ...patch,
  }) as PlotResult;

describe('runStatus', () => {
  it('names the session phases before the data', () => {
    expect(runStatus(initialAgentState('seaborn'), 'data', null).text).toBe('opening a session…');
    expect(runStatus(ready({ phase: 'ineligible' }), 'done', null)).toEqual({
      text: 'not eligible',
      tone: 'error',
    });
    const failed = runStatus(
      ready({ phase: 'error', failure: { code: 'capacity', ref: null } }),
      'done',
      null
    );
    expect(failed.text).toBe('error · capacity');
    expect(failed.detail).toMatch(/queue/);
    // A root call the model service refused after its retries ends as `capacity` too: the text says so.
    expect(failed.detail).toMatch(/model service is overloaded/);
    expect(runStatus(ready(), 'data', { code: 'rate_limited', ref: null }).text).toBe(
      'data · rate_limited'
    );
  });

  it('follows the data step, the wait for a place and the run', () => {
    expect(runStatus(ready(), 'data', null).text).toBe('storing the data…');
    expect(runStatus(ready(), 'waiting', null).text).toBe('waiting for a free place…');
    const run = { kind: 'create_plot' as const, steps: [], queue: null, stopping: false };
    expect(runStatus(ready({ run }), 'running', null).text).toBe('starting…');
    expect(
      runStatus(
        ready({
          run: {
            ...run,
            steps: [{ step: 'queued', attempt: null }],
            queue: { position: 2, waiting: 3 },
          },
        }),
        'running',
        null
      ).text
    ).toBe('queued · 2 of 3');
    expect(
      runStatus(
        ready({ run: { ...run, steps: [{ step: 'rendering', attempt: 1 }] } }),
        'running',
        null
      ).text
    ).toBe('rendering…');
    expect(runStatus(ready({ run: { ...run, stopping: true } }), 'running', null).text).toBe(
      'stopping…'
    );
  });

  it('ends on the version, or on what the run brought instead', () => {
    const version = {
      number: 1,
      library: 'seaborn',
      result: result({ status: 'needs_attention', attempts: 2 }),
      theme: 'light' as const,
      images: {},
      code: { state: 'loading' as const },
    };
    expect(runStatus(ready({ versions: { 1: version } }), 'done', null)).toEqual({
      text: 'v1 · needs attention · repaired',
      tone: 'warning',
    });
    expect(
      runStatus(ready({ versions: { 1: { ...version, result: result() } } }), 'done', null)
    ).toEqual({ text: 'v1 · ok', tone: 'ok' });

    const failed = result({ status: 'failed', reason: 'render_error' });
    expect(
      runStatus(ready({ items: [{ id: 1, kind: 'plot_failed', result: failed }] }), 'done', null)
        .text
    ).toBe('failed · render_error');
    // A model quota that outlasted the retries reads as busy, with the chat's sentence.
    const busy = result({ status: 'failed', reason: 'busy' });
    expect(
      runStatus(ready({ items: [{ id: 1, kind: 'plot_failed', result: busy }] }), 'done', null)
    ).toEqual({
      text: 'failed · busy',
      tone: 'error',
      detail: 'the model service is busy; try again in a minute',
    });
    expect(
      runStatus(
        ready({ items: [{ id: 1, kind: 'error', code: 'run_limit', ref: null }] }),
        'done',
        null
      ).text
    ).toBe('error · run_limit');
    expect(
      runStatus(
        ready({ items: [{ id: 1, kind: 'refusal', code: 'out_of_scope', text: 'no' }] }),
        'done',
        null
      ).text
    ).toBe('refused · out_of_scope');
    expect(
      runStatus(ready({ items: [{ id: 1, kind: 'notice', text: 'stopped' }] }), 'done', null).text
    ).toBe('stopped');
    expect(runStatus(ready(), 'done', null)).toEqual({ text: 'no plot', tone: 'error' });
  });
});
