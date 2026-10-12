import { describe, expect, it } from 'vitest';

import type { RunState, TimelineStep } from 'src/hooks/useAgentSession';
import type { Round } from 'src/lib/agent';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { gridRows, liveRows, outcomeText, roundLabel } from 'src/sections/agent-chat/timeline';
import { render, screen, within } from 'src/test-utils';

function run(steps: [TimelineStep, number | null][], extra: Partial<RunState> = {}): RunState {
  return {
    kind: 'create_plot',
    steps: steps.map(([step, attempt]) => ({ step, attempt })),
    queue: null,
    stopping: false,
    ...extra,
  };
}

/** A row as `label: step:state … | outcome`. */
const show = (rows: ReturnType<typeof gridRows>) =>
  rows.map(
    row =>
      `${row.label}: ${row.cells.map(cell => `${cell.step}:${cell.state}`).join(' ')}` +
      (row.outcome ? ` | ${row.outcome.text}` : '')
  );

const FIRST: [TimelineStep, number][] = [
  ['adapting', 1],
  ['checking', 1],
  ['rendering', 1],
  ['reviewing', 1],
];

describe('timeline grid', () => {
  it('shows the first try with the active step and the steps still to come', () => {
    expect(show(liveRows(run(FIRST.slice(0, 2))))).toEqual([
      'first try: adapting:done checking:active rendering:upcoming reviewing:upcoming',
    ]);
  });

  it('closes the first try with its outcome once the repair round starts', () => {
    // The owner's screenshot of 2026-10-12: every step again with "· attempt 2" read as many runs.
    const state = run([...FIRST, ['repairing', 2], ['checking', 2], ['rendering', 2]], {
      rounds: [{ attempt: 1, outcome: 'review', findings: 3 }],
    });

    expect(show(liveRows(state))).toEqual([
      'first try: adapting:done checking:done rendering:done reviewing:failed | ✗ review: 3 findings',
      'repair 1: repairing:done checking:done rendering:active reviewing:upcoming',
    ]);
  });

  it('marks the step a round stopped at and skips the ones after it', () => {
    const state = run(
      [
        ['adapting', 1],
        ['checking', 1],
        ['repairing', 2],
      ],
      { rounds: [{ attempt: 1, outcome: 'check_failed', findings: 2 }] }
    );

    expect(show(liveRows(state))[0]).toBe(
      'first try: adapting:done checking:failed rendering:skipped reviewing:skipped | ✗ code check failed'
    );
  });

  it('builds a finished grid from the outcomes alone, keeping the last findings open on needs_attention', () => {
    const rounds: Round[] = [
      { attempt: 1, outcome: 'measured', findings: 2 },
      { attempt: 2, outcome: 'review', findings: 1 },
    ];

    expect(show(gridRows(rounds, [], 'needs_attention'))).toEqual([
      'first try: adapting:done checking:done rendering:failed reviewing:skipped | ✗ 2 measured',
      'repair 1: repairing:done checking:done rendering:done reviewing:failed | ~ 1 finding open',
    ]);
    expect(show(gridRows([{ attempt: 1, outcome: 'ok', findings: 0 }], [], 'ok'))).toEqual([
      'first try: adapting:done checking:done rendering:done reviewing:done | ✓ ok',
    ]);
  });

  it("places an outcome at the step the server names, even where the outcome alone can't tell", () => {
    const rounds: Round[] = [
      { attempt: 1, outcome: 'unreviewed', findings: 0, step: 'reviewing', shipped: true },
    ];
    expect(show(gridRows(rounds, [], 'needs_attention'))).toEqual([
      'first try: adapting:done checking:done rendering:done reviewing:failed | ~ not reviewed',
    ]);
    const limit: Round[] = [{ attempt: 1, outcome: 'unreviewed', findings: 0, step: 'rendering' }];
    expect(show(gridRows(limit))[0]).toBe(
      'first try: adapting:done checking:done rendering:done reviewing:skipped | ~ not reviewed'
    );
    const late: Round[] = [{ attempt: 1, outcome: 'error', findings: 0, step: 'rendering' }];
    expect(show(gridRows(late))[0]).toBe(
      'first try: adapting:done checking:done rendering:failed reviewing:skipped | ✗ error'
    );
  });

  it('keeps the findings open on the round that shipped, not on a later round that failed', () => {
    const rounds: Round[] = [
      { attempt: 1, outcome: 'review', findings: 1, shipped: true },
      { attempt: 2, outcome: 'check_failed', findings: 2, shipped: false },
    ];

    expect(gridRows(rounds, [], 'needs_attention').map(row => row.outcome?.text)).toEqual([
      '~ 1 finding open',
      '✗ code check failed',
    ]);
  });

  it('names every outcome', () => {
    const texts = (
      [
        'ok',
        'review',
        'measured',
        'render_failed',
        'check_failed',
        'answer_unusable',
        'unreviewed',
        'error',
      ] as const
    ).map(outcome => outcomeText({ attempt: 1, outcome, findings: 2 }).text);
    expect(texts).toEqual([
      '✓ ok',
      '✗ review: 2 findings',
      '✗ 2 measured',
      '✗ render failed',
      '✗ code check failed',
      '✗ answer unusable',
      '~ not reviewed',
      '✗ error',
    ]);
    expect([1, 2, 3].map(roundLabel)).toEqual(['first try', 'repair 1', 'repair 2']);
  });
});

describe('ProgressTimeline', () => {
  it('lines the same steps up in columns, one row per round', () => {
    const state = run([...FIRST, ['repairing', 2], ['checking', 2]], {
      rounds: [{ attempt: 1, outcome: 'review', findings: 3 }],
    });
    render(<ProgressTimeline run={state} />);

    const rows = within(screen.getByRole('table', { name: 'Progress' })).getAllByRole('row');
    expect(rows).toHaveLength(2);
    const columns = rows.map(row =>
      within(row)
        .getAllByRole('cell')
        .slice(0, 4)
        .map(cell => cell.getAttribute('aria-label'))
    );
    expect(columns).toEqual([
      ['adapting, done', 'checking, done', 'rendering, done', 'reviewing, failed'],
      ['repairing, done', 'checking, in progress', 'rendering, next', 'reviewing, next'],
    ]);
    expect(screen.getByText('✗ review: 3 findings')).toBeInTheDocument();
    expect(screen.queryByText(/attempt/)).not.toBeInTheDocument();
  });

  it('shows the queue position while a plot run waits, above the path of its first try', () => {
    render(
      <ProgressTimeline run={run([['queued', null]], { queue: { position: 2, waiting: 3 } })} />
    );
    expect(screen.getByText('queued · 2 of 3')).toBeInTheDocument();
    const cells = within(screen.getByRole('table', { name: 'Progress' })).getAllByRole('cell');
    expect(cells.slice(0, 4).map(cell => cell.getAttribute('aria-label'))).toEqual([
      'adapting, next',
      'checking, next',
      'rendering, next',
      'reviewing, next',
    ]);
  });

  it('shows no grid for a turn that has not reached a pipeline step', () => {
    render(<ProgressTimeline run={run([['queued', null]], { kind: 'message' })} />);
    expect(screen.getByText('queued')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('says it is stopping after the current step', () => {
    render(<ProgressTimeline run={run(FIRST.slice(0, 1), { stopping: true })} />);
    expect(screen.getByText('stopping after this step…')).toBeInTheDocument();
  });
});
