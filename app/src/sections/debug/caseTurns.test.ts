import { describe, expect, it } from 'vitest';

import type { AgentCaseTurn, AgentCaseTurns } from 'src/lib/agent';
import {
  callLabel,
  endLine,
  guardSeverity,
  sharedTurns,
  turnChips,
  turnSeverity,
  turnsSummary,
} from 'src/sections/debug/caseTurns';

const turn = (overrides: Partial<AgentCaseTurn> = {}): AgentCaseTurn => ({
  turn: 1,
  action: 'text',
  kind: 'talk',
  refusal: null,
  error: null,
  tools: [],
  tools_dropped: 0,
  guards: [{ guard: 'scope_guard', verdict: 'in_scope' }],
  guards_dropped: 0,
  prep_ops: [],
  prep_ops_dropped: 0,
  ...overrides,
});

const profile = { tool: 'get_dataset_profile', verdict: 'allowed', outcome: 'ok', code: null };

/** An invented session: a question, a data change that failed once, a refused plot, a refusal before the judge. */
const TURNS: AgentCaseTurns = {
  records: [
    turn({ tools: [profile, profile] }),
    turn({
      turn: 2,
      kind: 'prep',
      tools: [
        { tool: 'prepare_data', verdict: 'allowed', outcome: 'error', code: 'invalid_operations' },
        { tool: 'prepare_data', verdict: 'allowed', outcome: 'changed', code: null },
      ],
      guards: [
        { guard: 'scope_guard', verdict: 'in_scope' },
        { guard: 'output_guard', verdict: 'reply_cut' },
      ],
      prep_ops: ['derive'],
    }),
    turn({
      turn: 3,
      action: 'create_plot',
      kind: 'plot',
      tools: [
        { tool: 'plot_pipeline', verdict: 'plot_as_confirmed', outcome: 'refused', code: null },
      ],
      guards: [],
    }),
    turn({
      turn: 4,
      kind: 'refused',
      refusal: 'rate_limited',
      guards: [{ guard: 'message_limit', verdict: 'rate_limited' }],
    }),
    turn({ turn: 4, kind: 'error', error: 'cancelled', guards: [] }),
  ],
  dropped: 2,
};

describe('turnSeverity', () => {
  it('flags an error answer, a cap, a refusal and a cancel', () => {
    expect(TURNS.records.map(turnSeverity)).toEqual(['ok', 'warn', 'warn', 'warn', 'warn']);
  });

  it('ranks a failed run, a broken tool, a failed turn and a lost reply as failures', () => {
    const failed = { tool: 'plot_pipeline', verdict: 'allowed', outcome: 'failed', code: 'render' };
    const raised = { tool: 'query_data', verdict: 'allowed', outcome: 'error', code: 'internal' };
    expect(turnSeverity(turn({ tools: [failed] }))).toBe('bad');
    expect(turnSeverity(turn({ tools: [raised] }))).toBe('bad');
    expect(turnSeverity(turn({ kind: 'error', error: 'guard_unavailable' }))).toBe('bad');
    expect(turnSeverity(turn({ guards: [{ guard: 'empty_reply', verdict: 'no_reply' }] }))).toBe(
      'bad'
    );
  });

  it('leaves a plot turn whose reply named no button unflagged', () => {
    const shipped = { tool: 'plot_pipeline', verdict: 'allowed', outcome: 'shipped', code: null };
    expect(turnSeverity(turn({ action: 'create_plot', kind: 'plot', tools: [shipped] }))).toBe(
      'ok'
    );
  });
});

describe('guardSeverity', () => {
  it('flags a reply that named the button, dropped or kept whole', () => {
    expect(guardSeverity('shipped_reply', 'dropped')).toBe('warn');
    expect(guardSeverity('shipped_reply', 'kept')).toBe('warn');
    expect(guardSeverity('plot_button', 'dropped')).toBe('warn');
    expect(guardSeverity('plot_button', 'kept')).toBe('warn');
  });

  it('passes a reply about the button the user asked for', () => {
    expect(guardSeverity('plot_button', 'asked')).toBe('ok');
  });
});

describe('turnChips', () => {
  const labels = (record: AgentCaseTurn) =>
    turnChips(record).map(chip => [chip.label, chip.severity, chip.count]);

  it('folds identical calls and leaves out the guards that passed', () => {
    expect(labels(TURNS.records[0])).toEqual([['get_dataset_profile', 'ok', 2]]);
    expect(labels(TURNS.records[1])).toEqual([
      ['output_guard: reply_cut', 'warn', 1],
      ['prepare_data: error · invalid_operations', 'warn', 1],
      ['prepare_data: changed', 'ok', 1],
    ]);
  });

  it('names a refused call by its verdict', () => {
    expect(labels(TURNS.records[2])).toEqual([
      ['plot_pipeline refused: plot_as_confirmed', 'warn', 1],
    ]);
  });

  it('names the turn end only when no guard chip does', () => {
    expect(labels(TURNS.records[3])).toEqual([['message_limit: rate_limited', 'warn', 1]]);
    expect(labels(TURNS.records[4])).toEqual([['error: cancelled', 'warn', 1]]);
  });
});

describe('the matrix lines', () => {
  it('sums up the turns', () => {
    expect(turnsSummary(TURNS)).toBe('5 turns · 4 flagged · 2 older not kept');
    expect(
      turnsSummary({ records: [turn(), turn({ kind: 'error', error: 'deadline' })], dropped: 0 })
    ).toBe('2 turns · 1 failed');
  });

  it('writes how a turn ended', () => {
    expect(endLine(TURNS.records[3])).toBe('message → refused (rate_limited)');
    expect(endLine(turn({ action: 'create_plot', kind: 'plot' }))).toBe('create_plot → plot');
  });

  it('finds the turn number two records share', () => {
    expect([...sharedTurns(TURNS)]).toEqual([4]);
  });

  it('writes a call with its outcome and code', () => {
    expect(
      callLabel({ tool: 'plot_pipeline', verdict: 'allowed', outcome: 'failed', code: 'render' })
    ).toBe('plot_pipeline: failed · render');
  });
});
