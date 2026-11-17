import { describe, expect, it } from 'vitest';

import type {
  AgentCaseCallShape,
  AgentCaseOperation,
  AgentCaseTurn,
  AgentCaseTurns,
} from 'src/lib/agent';
import {
  callLabel,
  endLine,
  guardSeverity,
  operationLabel,
  shapeLines,
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

  it('flags a refused call also when its verdict did not arrive', () => {
    const refused = { tool: 'plot_pipeline', verdict: 'allowed', outcome: 'refused', code: null };
    expect(turnSeverity(turn({ tools: [refused] }))).toBe('warn');
    expect(callLabel(refused)).toBe('plot_pipeline: refused');
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

  it('passes a reply whose figures stood in a source and fails one that was withheld', () => {
    expect(guardSeverity('number_provenance', 'clean')).toBe('ok');
    expect(guardSeverity('number_provenance', 'unsourced_logged')).toBe('warn');
    expect(guardSeverity('number_provenance', 'reasked')).toBe('warn');
    expect(guardSeverity('number_provenance', 'kept')).toBe('warn');
    expect(guardSeverity('number_provenance', 'withheld')).toBe('bad');
    // The check itself failed and the reply went out unchecked: shown as a failure, so it is seen.
    expect(guardSeverity('number_provenance', 'error')).toBe('bad');
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

  it('shows one chip for a withheld reply, the figure check’s own', () => {
    const withheld = turn({
      kind: 'error',
      error: 'unverified_figure',
      guards: [{ guard: 'number_provenance', verdict: 'withheld' }],
    });
    expect(labels(withheld)).toEqual([['number_provenance: withheld', 'bad', 1]]);
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

  it('finds the turn numbers several records share, with how many', () => {
    expect([...sharedTurns(TURNS)]).toEqual([[4, 2]]);
    const limited = turn({ turn: 2, kind: 'refused', refusal: 'rate_limited', guards: [] });
    expect([
      ...sharedTurns({ records: [turn(), limited, limited, turn({ turn: 2 })], dropped: 0 }),
    ]).toEqual([[2, 3]]);
  });

  it('writes a call with its outcome and code', () => {
    expect(
      callLabel({ tool: 'plot_pipeline', verdict: 'allowed', outcome: 'failed', code: 'render' })
    ).toBe('plot_pipeline: failed · render');
  });
});

const operation = (overrides: Partial<AgentCaseOperation>): AgentCaseOperation => ({
  op: 'sort',
  mode: null,
  target: null,
  order: null,
  conditions: null,
  how: null,
  period: null,
  keys: null,
  type: null,
  date_format: null,
  decimal: null,
  unit: null,
  keep: null,
  family: null,
  ...overrides,
});

const shape = (overrides: Partial<AgentCaseCallShape>): AgentCaseCallShape => ({
  operations: null,
  from_version: null,
  limit: null,
  base: null,
  theme: null,
  combine: null,
  change_request: null,
  expected_texts: null,
  remember: null,
  applies_to: null,
  plot: null,
  ...overrides,
});

describe('the shape of a call', () => {
  it('writes an operation with its codes and its conditions, each part labelled', () => {
    const selection = operation({
      op: 'keep_rows',
      mode: 'where',
      target: 'plot',
      conditions: [
        { test: 'ge', value_shape: 'iso_date', column_kind: 'datetime' },
        { test: 'eq', value_shape: 'list', column_kind: 'text' },
      ],
    });
    expect(operationLabel(selection)).toBe(
      'keep_rows · mode: where · target: plot · conditions: datetime column ge iso_date value, text column eq list value'
    );
    const dropped = operation({
      op: 'drop_rows',
      conditions: [{ test: 'not_missing', value_shape: 'none', column_kind: 'integer' }],
    });
    expect(operationLabel(dropped)).toBe('drop_rows · conditions: integer column not_missing');
    expect(
      operationLabel(operation({ op: 'aggregate', how: 'sum', period: 'month', keys: 2 }))
    ).toBe('aggregate · how: sum · period: month · keys: 2');
    expect(operationLabel(operation({ op: 'rename' }))).toBe('rename');
  });

  it('names a decimal mark and a column whose kind is unknown', () => {
    expect(operationLabel(operation({ op: 'set_type', type: 'number', decimal: ',' }))).toBe(
      'set_type · type: number · decimal: comma'
    );
    expect(operationLabel(operation({ op: 'set_type', type: 'number', decimal: '.' }))).toBe(
      'set_type · type: number · decimal: dot'
    );
    const selection = operation({
      op: 'keep_rows',
      mode: 'where',
      conditions: [{ test: 'eq', value_shape: 'text', column_kind: 'unknown' }],
    });
    expect(operationLabel(selection)).toBe(
      'keep_rows · mode: where · conditions: unknown-kind column eq text value'
    );
  });

  it('writes the call’s own codes first, then one line per operation', () => {
    const question = shape({
      from_version: 'current',
      limit: false,
      operations: [operation({ op: 'apply_view' }), operation({ op: 'sort', order: 'descending' })],
    });
    expect(shapeLines(question)).toEqual([
      'from_version: current · limit: default',
      'apply_view',
      'sort · order: descending',
    ]);
    expect(shapeLines(shape({ from_version: 'numbered', limit: true }))).toEqual([
      'from_version: numbered · limit: named',
    ]);
    const run = shape({
      base: 'previous',
      change_request: true,
      expected_texts: 2,
      remember: ['title', 'scale'],
    });
    expect(shapeLines(run)).toEqual([
      'base: previous · change_request: yes · expected_texts: 2 · remember: title, scale',
    ]);
    expect(shapeLines(shape({ change_request: false, expected_texts: 0 }))).toEqual([
      'change_request: no · expected_texts: 0',
    ]);
    expect(shapeLines(shape({ plot: false }))).toEqual(['plot: later']);
    expect(shapeLines(shape({ plot: true }))).toEqual(['plot: at once']);
  });

  it('has no line for a call without a shape or with an empty list only', () => {
    expect(shapeLines(null)).toEqual([]);
    expect(shapeLines(undefined)).toEqual([]);
    expect(shapeLines(shape({ remember: [] }))).toEqual([]);
  });
});
