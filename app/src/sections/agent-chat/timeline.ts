/**
 * The progress grid of a plot run (`ProgressTimeline.tsx` while it runs, the
 * result card afterwards): one row per round, the same four steps in the same
 * columns, and how the round ended on the right. The first try runs adapting,
 * checking, rendering and reviewing; a repair round runs repairing in the first
 * column, then the same three. The owner's choice of 2026-10-12 (variant A):
 * every step stays visible and lines up under the step of the round above, and
 * a finished round says ok or not ok and why, instead of repeating each step
 * with its attempt number.
 *
 * A finished round's cells come from the steps the run reported for it when the
 * page saw them, else from its outcome alone (a result card's `rounds`): the
 * step it stopped at is failed, the steps after it were skipped.
 */

import type { RunState } from 'src/hooks/useAgentSession';
import type { PipelineStep, PlotStatus, Round, RoundOutcome } from 'src/lib/agent';

const FIRST_TRY: PipelineStep[] = ['adapting', 'checking', 'rendering', 'reviewing'];
const REPAIR: PipelineStep[] = ['repairing', 'checking', 'rendering', 'reviewing'];

/** The short names a phone-width grid shows, so four columns fit beside the round label. */
export const SHORT_STEP: Record<PipelineStep, string> = {
  adapting: 'adapt',
  repairing: 'repair',
  checking: 'check',
  rendering: 'render',
  reviewing: 'review',
};

/** The column a round stopped at, by its outcome, when the page did not see its steps. */
const STOP_COLUMN: Record<RoundOutcome, number> = {
  ok: 3,
  review: 3,
  measured: 2,
  render_failed: 2,
  check_failed: 1,
  answer_unusable: 0,
  unreviewed: 2,
  error: 0,
};

export type CellState = 'done' | 'active' | 'failed' | 'skipped' | 'upcoming';

export interface GridCell {
  step: PipelineStep;
  state: CellState;
}

export type OutcomeTone = 'ok' | 'failed' | 'open';

export interface GridRow {
  attempt: number;
  label: string;
  cells: GridCell[];
  /** How the round ended, or `null` while it runs. */
  outcome: { text: string; tone: OutcomeTone } | null;
}

/** The name of a pipeline round: attempt 1 is the first try, every later attempt a repair. */
export function roundLabel(attempt: number): string {
  return attempt <= 1 ? 'first try' : `repair ${attempt - 1}`;
}

const plural = (count: number, noun: string) => `${count} ${noun}${count === 1 ? '' : 's'}`;

/**
 * The text and tone of a round's end. The shipped round of a result that still
 * had findings (`needs_attention`) keeps them open rather than failed.
 */
export function outcomeText(round: Round, open = false): { text: string; tone: OutcomeTone } {
  const count = Math.max(round.findings, 1);
  switch (round.outcome) {
    case 'ok':
      return { text: '✓ ok', tone: 'ok' };
    case 'review':
      return open
        ? { text: `~ ${plural(count, 'finding')} open`, tone: 'open' }
        : { text: `✗ review: ${plural(count, 'finding')}`, tone: 'failed' };
    case 'measured':
      return open
        ? { text: `~ ${count} measured open`, tone: 'open' }
        : { text: `✗ ${count} measured`, tone: 'failed' };
    case 'render_failed':
      return { text: '✗ render failed', tone: 'failed' };
    case 'check_failed':
      return { text: '✗ code check failed', tone: 'failed' };
    case 'answer_unusable':
      return { text: '✗ answer unusable', tone: 'failed' };
    case 'unreviewed':
      return { text: '~ not reviewed', tone: 'open' };
    case 'error':
      return { text: '✗ error', tone: 'failed' };
  }
}

function columnOf(step: PipelineStep): number {
  return step === 'repairing' ? 0 : FIRST_TRY.indexOf(step);
}

function finishedCells(names: PipelineStep[], round: Round, reached: PipelineStep[]): GridCell[] {
  const stop = reached.length ? columnOf(reached[reached.length - 1]) : STOP_COLUMN[round.outcome];
  const passed = round.outcome === 'ok' || round.outcome === 'unreviewed';
  return names.map((step, column) => ({
    step,
    state: column < stop ? 'done' : column > stop ? 'skipped' : passed ? 'done' : 'failed',
  }));
}

function liveCells(names: PipelineStep[], reached: PipelineStep[]): GridCell[] {
  const current = reached.length ? columnOf(reached[reached.length - 1]) : -1;
  return names.map((step, column) => ({
    step,
    state: column < current ? 'done' : column === current ? 'active' : 'upcoming',
  }));
}

/**
 * The rows of a grid. `rounds` are the rounds that ended; `steps` the steps the
 * page saw (a running turn); `status` the shipped result's status, which keeps
 * the shipped round's findings open on `needs_attention` (the round the server
 * marks `shipped`, which a repair that failed its check leaves earlier than the
 * last). A running round without
 * an outcome is the last row, with its active step and the steps still to come.
 */
export function gridRows(
  rounds: Round[],
  steps: RunState['steps'] = [],
  status: PlotStatus | null = null
): GridRow[] {
  const reachedBy = new Map<number, PipelineStep[]>();
  for (const entry of steps) {
    if (entry.step === 'queued') continue;
    const attempt = entry.attempt ?? 1;
    reachedBy.set(attempt, [...(reachedBy.get(attempt) ?? []), entry.step]);
  }
  const attempts = [...new Set([...rounds.map(round => round.attempt), ...reachedBy.keys()])].sort(
    (a, b) => a - b
  );
  // The round whose render shipped: the server marks it; an older result without the mark means the last.
  const shippedRound =
    rounds.find(round => round.shipped)?.attempt ??
    (rounds.some(round => round.shipped !== undefined) ? null : rounds[rounds.length - 1]?.attempt);
  return attempts.map(attempt => {
    const names = attempt > 1 ? REPAIR : FIRST_TRY;
    const reached = reachedBy.get(attempt) ?? [];
    const round = rounds.find(item => item.attempt === attempt);
    if (!round) {
      return {
        attempt,
        label: roundLabel(attempt),
        cells: liveCells(names, reached),
        outcome: null,
      };
    }
    const open = status === 'needs_attention' && attempt === shippedRound;
    return {
      attempt,
      label: roundLabel(attempt),
      cells: finishedCells(names, round, reached),
      outcome: outcomeText(round, open),
    };
  });
}

/**
 * The grid of a running turn: its finished rounds and the round in progress. A
 * `create_plot` run shows its first try's path before the first step arrives
 * (while it starts or waits in the queue); any other turn shows rows only once
 * it reached a pipeline step.
 */
export function liveRows(run: RunState): GridRow[] {
  const rows = gridRows(run.rounds ?? [], run.steps);
  if (rows.length || run.kind !== 'create_plot') return rows;
  return [{ attempt: 1, label: roundLabel(1), cells: liveCells(FIRST_TRY, []), outcome: null }];
}
