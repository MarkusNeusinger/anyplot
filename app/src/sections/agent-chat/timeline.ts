/**
 * The entries of the progress timeline (`ProgressTimeline.tsx`), computed from
 * the run's `status` steps. The first try runs adapting, checking, rendering and
 * reviewing; a repair round runs repairing, checking, rendering and reviewing.
 * A finished round folds into one entry (`first try done`, `repair 1 done`), so
 * a repair reads as one more round, not as every step again with its attempt
 * number (the owner's feedback of 2026-10-12: the way the attempts were shown
 * looked odd, as if the run tried many times).
 */

import type { RunState, TimelineStep } from 'src/hooks/useAgentSession';

const FIRST_TRY: TimelineStep[] = ['adapting', 'checking', 'rendering', 'reviewing'];
const REPAIR: TimelineStep[] = ['repairing', 'checking', 'rendering', 'reviewing'];

/** `done` is a finished round folded into one entry, shown without a dot. */
export type ItemState = 'done' | 'past' | 'active' | 'upcoming';

export interface TimelineItem {
  key: string;
  label: string;
  state: ItemState;
}

/** The name of a pipeline round: attempt 1 is the first try, every later attempt a repair. */
export function roundLabel(attempt: number): string {
  return attempt <= 1 ? 'first try' : `repair ${attempt - 1}`;
}

/** The entries in order: the queue, the finished rounds, the current round, its next steps (plot runs only). */
export function timelineItems(run: RunState): TimelineItem[] {
  const last = run.steps.length - 1;
  const attemptOf = (attempt: number | null) => attempt ?? 1;
  const pipeline = run.steps.filter(entry => entry.step !== 'queued');
  const round = pipeline.length ? attemptOf(pipeline[pipeline.length - 1].attempt) : 1;
  const items: TimelineItem[] = [];
  const folded = new Set<number>();
  run.steps.forEach((entry, index) => {
    const state: ItemState = index === last ? 'active' : 'past';
    if (entry.step === 'queued') {
      const label =
        state === 'active' && run.queue
          ? `queued · ${run.queue.position} of ${run.queue.waiting}`
          : 'queued';
      items.push({ key: `queued-${index}`, label, state });
      return;
    }
    const attempt = attemptOf(entry.attempt);
    if (attempt < round) {
      if (!folded.has(attempt)) {
        folded.add(attempt);
        items.push({
          key: `round-${attempt}`,
          label: `${roundLabel(attempt)} done`,
          state: 'done',
        });
      }
      return;
    }
    items.push({ key: `${entry.step}-${index}`, label: entry.step, state });
  });
  if (run.kind === 'create_plot') {
    const reached = new Set(
      pipeline.filter(entry => attemptOf(entry.attempt) === round).map(entry => entry.step)
    );
    for (const step of round > 1 ? REPAIR : FIRST_TRY) {
      if (!reached.has(step)) items.push({ key: `next-${step}`, label: step, state: 'upcoming' });
    }
  }
  return items;
}
