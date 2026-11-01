import { describe, expect, it } from 'vitest';

import { type AgentSessionState, initialAgentState } from 'src/hooks/useAgentSession';
import type { PlotResult } from 'src/lib/agent';
import {
  awaitsRetry,
  type FanOutSlot,
  type FanOutState,
  grantSlots,
  initialFanOut,
  nextFanOut,
  RUN_LIMIT_GIVE_UP_MS,
  RUN_LIMIT_RETRY_MS,
  runStatus,
} from 'src/sections/agent-chat/fanoutRules';

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

  it('says a library the cap refused waits, and says when it gave up', () => {
    const limited = ready({ items: [{ id: 1, kind: 'error', code: 'run_limit', ref: null }] });

    expect(runStatus(limited, 'waiting', null, { count: 2, gaveUp: false })).toMatchObject({
      text: 'waiting · run_limit ×2',
      tone: 'muted',
    });
    expect(runStatus(limited, 'done', null, { count: 40, gaveUp: true })).toMatchObject({
      text: 'gave up · run_limit',
      tone: 'error',
      detail: expect.stringContaining('30 minutes'),
    });
  });
});

/** A panel of `libraries` whose data is stored: every library waits, `max` of them start. */
function storedPanel(libraries: readonly string[], max: number): FanOutState {
  return libraries.reduce(
    (state, library) => nextFanOut(state, { type: 'ready', library }, libraries, max),
    initialFanOut(libraries)
  );
}

describe('nextFanOut', () => {
  it('sends a library the cap refused back to waiting and starts nothing past the runs the server took', () => {
    let panel = storedPanel(ORDER, 2);
    expect(panel.slots).toMatchObject({ matplotlib: 'running', seaborn: 'running' });

    panel = nextFanOut(panel, { type: 'run_limit', library: 'seaborn', now: 0 }, ORDER, 2);

    expect(panel.slots).toEqual({
      matplotlib: 'running',
      seaborn: 'waiting',
      plotnine: 'waiting',
      altair: 'waiting',
    });
    expect(panel.cap).toBe(1);
    expect(panel.limited.seaborn).toEqual({ since: 0, count: 1 });
    expect(awaitsRetry(panel)).toBe(true);
  });

  it('gives a freed place to the first waiting library, and a retry one library more', () => {
    let panel = storedPanel(ORDER, 2);
    panel = nextFanOut(panel, { type: 'run_limit', library: 'seaborn', now: 0 }, ORDER, 2);

    panel = nextFanOut(panel, { type: 'ended', library: 'matplotlib' }, ORDER, 2);
    expect(panel.slots).toMatchObject({ seaborn: 'running', plotnine: 'waiting' });

    panel = nextFanOut(panel, { type: 'retry' }, ORDER, 2);
    expect(panel.slots).toMatchObject({ seaborn: 'running', plotnine: 'running' });
    expect(panel.cap).toBeNull(); // back at the server's cap
  });

  it('gives up on a library only after half an hour of run_limit', () => {
    let panel = storedPanel(ORDER, 1);
    panel = nextFanOut(panel, { type: 'run_limit', library: 'matplotlib', now: 0 }, ORDER, 1);
    panel = nextFanOut(panel, { type: 'retry' }, ORDER, 1);
    panel = nextFanOut(
      panel,
      { type: 'run_limit', library: 'matplotlib', now: RUN_LIMIT_GIVE_UP_MS - 1 },
      ORDER,
      1
    );
    expect(panel.slots.matplotlib).toBe('waiting');

    panel = nextFanOut(panel, { type: 'retry' }, ORDER, 1);
    panel = nextFanOut(
      panel,
      { type: 'run_limit', library: 'matplotlib', now: RUN_LIMIT_GIVE_UP_MS },
      ORDER,
      1
    );
    expect(panel.slots.matplotlib).toBe('done');
    expect(panel.gaveUp).toEqual(['matplotlib']);
    expect(panel.limited.matplotlib.count).toBe(3);
  });

  it('ignores the events of a library that is done', () => {
    let panel = storedPanel(ORDER, 2);
    panel = nextFanOut(panel, { type: 'ended', library: 'matplotlib' }, ORDER, 2);

    expect(nextFanOut(panel, { type: 'run_limit', library: 'matplotlib', now: 0 }, ORDER, 2)).toBe(
      panel
    );
  });
});

describe('three panels sharing one cap', () => {
  /**
   * The owner's question of 2026-11-01: an admin starts `.plot_all()` in three windows at once. The server
   * takes at most `serverCap` of the admin's runs in all; a turn it refuses ends after `refuseS` with
   * `run_limit`, a turn it takes ends after `runS`. Every panel retries every 15 s while held back. One second
   * per step until all libraries ended.
   */
  function simulate(panels: number, libraries: number, serverCap: number, runS = 90, refuseS = 3) {
    const order = Array.from({ length: libraries }, (_, index) => `lib${index}`);
    const states = Array.from({ length: panels }, () => storedPanel(order, serverCap));
    const turns = new Map<
      string,
      { panel: number; library: string; endsAt: number; taken: boolean }
    >();
    let inFlight = 0;
    let refused = 0;
    let lastRetry = 0;
    let now = 0;
    const startTurns = () => {
      states.forEach((state, panel) => {
        for (const library of order) {
          const key = `${panel}/${library}`;
          if (state.slots[library] !== 'running' || turns.has(key)) continue;
          const taken = inFlight < serverCap;
          if (taken) inFlight += 1;
          turns.set(key, { panel, library, endsAt: now + (taken ? runS : refuseS), taken });
        }
      });
    };
    startTurns();
    while (states.some(state => Object.values(state.slots).some(slot => slot !== 'done'))) {
      now += 1;
      for (const [key, turn] of [...turns]) {
        if (turn.endsAt > now) continue;
        turns.delete(key);
        if (turn.taken) inFlight -= 1;
        else refused += 1;
        const event = turn.taken
          ? ({ type: 'ended', library: turn.library } as const)
          : ({ type: 'run_limit', library: turn.library, now: now * 1000 } as const);
        states[turn.panel] = nextFanOut(states[turn.panel], event, order, serverCap);
      }
      if ((now - lastRetry) * 1000 >= RUN_LIMIT_RETRY_MS) {
        lastRetry = now;
        states.forEach((state, panel) => {
          if (awaitsRetry(state))
            states[panel] = nextFanOut(state, { type: 'retry' }, order, serverCap);
        });
      }
      startTurns();
      if (now > 3 * 3600) throw new Error('the panels never finished');
    }
    return { minutes: now / 60, refused, gaveUp: states.flatMap(state => state.gaveUp) };
  }

  it('finishes all 45 plots of three 15-library panels without one lost to run_limit', () => {
    const { minutes, refused, gaveUp } = simulate(3, 15, 5);

    expect(gaveUp).toEqual([]);
    // 45 runs of 90 s through five places take 13.5 minutes at best; the retries keep it close.
    expect(minutes).toBeGreaterThanOrEqual(13.5);
    expect(minutes).toBeLessThan(18);
    // The panels back off instead of burning their libraries: at most a few refused turns a minute.
    expect(refused / minutes).toBeLessThan(15);
  });

  it('runs one panel at the full cap without a single refusal', () => {
    const { refused, gaveUp, minutes } = simulate(1, 15, 5);

    expect(gaveUp).toEqual([]);
    expect(refused).toBe(0);
    expect(minutes).toBeCloseTo(4.5, 0);
  });
});
