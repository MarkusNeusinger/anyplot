/**
 * The progress of the running turn, from its `status` events: the wait in the
 * run queue (with the position) as one line, then the rounds of the pipeline as
 * a grid (`RoundGrid`, `timeline.ts`): one row per round with its steps in
 * fixed columns, the active step marked, the steps still to come muted, and a
 * finished round's outcome on the right (from the repair step's `outcome`).
 *
 * The page mounts it for a `create_plot` run and for any turn that waits in
 * the queue or reached a pipeline step (`showsTimeline` in `steps.ts`). A turn
 * without steps, the summary or a question, has the thread's in-progress line
 * instead, so `starting…` and a step-less `stopping…` belong to plot runs.
 */

import Box from '@mui/material/Box';

import type { RunState } from 'src/hooks/useAgentSession';
import { RoundGrid } from 'src/sections/agent-chat/RoundGrid';
import { liveRows } from 'src/sections/agent-chat/timeline';
import { colors, fontSize, typography } from 'src/theme';

export function ProgressTimeline({ run }: { run: RunState }) {
  const rows = liveRows(run);
  const waiting = run.steps[run.steps.length - 1]?.step === 'queued';
  const started = run.steps.some(entry => entry.step !== 'queued');
  // Before the first pipeline step: the queue position, or that the run is starting.
  const before = waiting
    ? run.queue
      ? `queued · ${run.queue.position} of ${run.queue.waiting}`
      : 'queued'
    : started
      ? null
      : 'starting…';
  // A stopped run ends at its next step boundary; the server's `done` confirms it.
  const stopping = run.stopping
    ? waiting
      ? 'leaving the queue…'
      : started
        ? 'stopping after this step…'
        : 'stopping…'
    : null;

  return (
    <Box
      aria-live="polite"
      sx={{ display: 'grid', gap: 0.75, fontFamily: typography.mono, fontSize: fontSize.md }}
    >
      {before && !(stopping && !waiting) && (
        <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, color: 'var(--ink)' }}>
          <Box
            component="span"
            aria-hidden
            sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: colors.primary }}
          />
          {before}
        </Box>
      )}
      {rows.length > 0 && <RoundGrid rows={rows} label="Progress" />}
      {stopping && <Box sx={{ color: 'var(--ink-muted)' }}>{stopping}</Box>}
    </Box>
  );
}
