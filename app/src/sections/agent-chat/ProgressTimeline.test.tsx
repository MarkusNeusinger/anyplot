import { describe, expect, it } from 'vitest';

import type { RunState, TimelineStep } from 'src/hooks/useAgentSession';
import type { Round } from 'src/lib/agent';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import {
  gridRows,
  liveRows,
  outcomeText,
  roundLabel,
  triesText,
} from 'src/sections/agent-chat/timeline';
import { render, screen, styleAt, within } from 'src/test-utils';

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
      (row.outcome ? ` | ${row.outcome.text}` : row.repairs ? ` | ${row.repairs}` : '')
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
      // A review that found things to fix did its work: the repair below it is the normal course.
      'first try: adapting:done checking:done rendering:done reviewing:done | 3 things to fix',
      'second try: repairing:done checking:done rendering:active reviewing:upcoming | fixing what the review found',
    ]);
  });

  it('names what a repair round repairs in words while it runs', () => {
    // Live round 9 of 2026-10-16: a forced repair of VQ-01 and VQ-05 ran and the page showed only the first try.
    const state = run([...FIRST, ['repairing', 2]], {
      rounds: [
        { attempt: 1, outcome: 'review', findings: 2, defects: ['VQ-01', 'VQ-05', 'ZZ-99'] },
      ],
    });

    expect(show(liveRows(state))[1]).toBe(
      'second try: repairing:active checking:upcoming rendering:upcoming reviewing:upcoming | fixing text size, layout'
    );
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
      'first try: adapting:done checking:done rendering:done reviewing:skipped | 2 things to fix',
      'second try: repairing:done checking:done rendering:done reviewing:done | ~ 1 note left',
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
      '~ 1 note left',
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
      '2 things to fix',
      '2 things to fix',
      '✗ render failed',
      '✗ code check failed',
      '✗ answer unusable',
      '~ not reviewed',
      '✗ error',
    ]);
    expect([1, 2, 3, 6].map(roundLabel)).toEqual(['first try', 'second try', 'third try', 'try 6']);
  });

  it("names the card's tries, and which round shipped when an earlier one won", () => {
    expect(
      triesText({
        attempts: 1,
        rounds: [{ attempt: 1, outcome: 'ok', findings: 0, shipped: true }],
      })
    ).toBe('first try');
    const won = (shipped: number): Round[] =>
      [1, 2].map(attempt => ({
        attempt,
        outcome: 'review',
        findings: 1,
        shipped: attempt === shipped,
      }));
    expect(triesText({ attempts: 2, rounds: won(2) })).toBe('second try');
    expect(triesText({ attempts: 2, rounds: won(1) })).toBe('first try shipped of 2');
    expect(triesText({ attempts: 2, rounds: won(0) })).toBe('2 tries'); // nothing shipped
    expect(triesText({ attempts: 2 })).toBe('second try'); // an older result without rounds
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
      ['adapting, done', 'checking, done', 'rendering, done', 'reviewing, done'],
      ['repairing, done', 'checking, in progress', 'rendering, next', 'reviewing, next'],
    ]);
    // A normal repair reads as the loop's course: neutral ink, no red ✗ anywhere in the grid.
    expect(styleAt(screen.getByText('3 things to fix')).color).toBe('var(--ink-soft)');
    expect(screen.queryByText('✗')).not.toBeInTheDocument();
    expect(screen.queryByText(/attempt/)).not.toBeInTheDocument();
  });

  it('shows the queue position while a plot run waits, in the row of its first try', () => {
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

  it('keeps the grid first from the start of a plot run to its steps, with the wait in its first row', () => {
    // A `starting…` line above the grid went away at the first step: the grid jumped up a line.
    const states: [RunState, string][] = [
      [run([]), 'starting…'],
      [run([['queued', null]], { queue: { position: 2, waiting: 3 } }), 'queued · 2 of 3'],
      [run([['queued', null]], { queue: { position: 1, waiting: 2 } }), 'queued · 1 of 2'],
      [run([['queued', null], ...FIRST.slice(0, 1)]), ''],
      [run([['queued', null], ...FIRST.slice(0, 2)]), ''],
    ];
    const { rerender } = render(<ProgressTimeline run={states[0][0]} />);
    const grid = screen.getByRole('table', { name: 'Progress' });
    for (const [state, status] of states) {
      rerender(<ProgressTimeline run={state} />);
      // The same grid throughout, and nothing above it in the live region that could come or go.
      expect(screen.getByRole('table', { name: 'Progress' })).toBe(grid);
      expect(grid.parentElement?.firstElementChild).toBe(grid);
      const cells = within(within(grid).getAllByRole('row')[0]).getAllByRole('cell');
      expect(cells[cells.length - 1].textContent).toBe(status);
    }
  });

  it("turns the page's scroll anchoring off while the run lasts, and back after it", () => {
    // A repair round's row grew the grid, and the browser scrolled the page to hold a node below
    // it: the loader and the rows already shown jumped up by that row.
    const root = document.documentElement;
    root.style.overflowAnchor = 'auto';
    const first = render(<ProgressTimeline run={run(FIRST.slice(0, 1))} />);
    expect(root.style.overflowAnchor).toBe('none');
    // Two at once (none today) hold it off until the last one goes, then the page's value is back.
    const second = render(<ProgressTimeline run={run(FIRST.slice(0, 2))} />);
    first.unmount();
    expect(root.style.overflowAnchor).toBe('none');
    second.unmount();
    expect(root.style.overflowAnchor).toBe('auto');
    root.style.overflowAnchor = '';
  });

  it('adds a stop below the grid, keeping the queue position in its row', () => {
    const { rerender } = render(<ProgressTimeline run={run([], { stopping: true })} />);
    const grid = screen.getByRole('table', { name: 'Progress' });
    expect(grid.parentElement?.firstElementChild).toBe(grid);
    expect(grid.nextElementSibling).toHaveTextContent('stopping…');
    expect(screen.queryByText('starting…')).not.toBeInTheDocument();

    rerender(
      <ProgressTimeline
        run={run([['queued', null]], { queue: { position: 2, waiting: 3 }, stopping: true })}
      />
    );
    expect(grid.parentElement?.firstElementChild).toBe(grid);
    expect(within(grid).getByText('queued · 2 of 3')).toBeInTheDocument();
    expect(grid.nextElementSibling).toHaveTextContent('leaving the queue…');
  });

  it('keeps the widths of the step cells, whatever their state and whichever round', () => {
    // A step without a mark had a narrower cell: each step that turned active pushed the ones after it.
    render(<ProgressTimeline run={run(FIRST.slice(0, 1))} />);
    const cells = within(screen.getByRole('table', { name: 'Progress' }))
      .getAllByRole('cell')
      .slice(0, 4);
    expect(cells.map(cell => within(cell).queryAllByTestId('step-marker').length)).toEqual([
      1, 1, 1, 1,
    ]);
    // The first column holds a repair round's longer name unseen, so that row never widens it.
    const ghost = within(cells[0]).getByText('repairing').closest('[aria-hidden="true"]');
    expect(ghost).not.toBeNull();
    expect(ghost).toContainElement(within(cells[0]).getByText('repair'));
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

  it('says a cut stream reconnects below the grid, quietly, until a stop says more', () => {
    const { unmount } = render(
      <ProgressTimeline run={run(FIRST.slice(0, 2), { reconnecting: true })} />
    );
    const grid = screen.getByRole('table', { name: 'Progress' });
    expect(grid.nextElementSibling).toHaveTextContent(/^connection lost · reconnecting…$/);
    expect(styleAt(grid.nextElementSibling!).color).toBe('var(--ink-muted)');
    expect(screen.getByTestId('loader-spinner')).toBeInTheDocument();
    unmount();
    render(
      <ProgressTimeline run={run(FIRST.slice(0, 2), { reconnecting: true, stopping: true })} />
    );
    expect(screen.queryByText('connection lost · reconnecting…')).not.toBeInTheDocument();
    expect(screen.getByText('stopping after this step…')).toBeInTheDocument();
  });

  it('shows the site loader beside the run, outside its live region, from the queue to the stop', () => {
    const { unmount } = render(<ProgressTimeline run={run([['queued', null]])} />);
    const loader = screen.getByTestId('loader-spinner');
    expect(loader).toHaveAttribute('aria-hidden', 'true');
    expect(loader).toHaveAttribute('data-size', 'inline');
    // The live region announces the words and the grid; the dots never join it.
    expect(loader.closest('[aria-live]')).toBeNull();
    unmount();

    render(<ProgressTimeline run={run(FIRST.slice(0, 1), { stopping: true })} />);
    expect(screen.getByTestId('loader-spinner')).toBeInTheDocument();
  });
});
