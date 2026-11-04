/**
 * The progress of the running turn, from its `status` events: the wait in the
 * run queue (with the position) as one line, then the rounds of the pipeline as
 * a grid (`RoundGrid`, `timeline.ts`): one row per round with its steps in
 * fixed columns, the active step marked, the steps still to come muted, and a
 * finished round's outcome on the right (from the repair step's `outcome`).
 * The site's loader stands beside it while the run lasts, also while it stops.
 *
 * The page mounts it for a plot run, from the queue on, and for any turn that
 * reached a pipeline step (`showsTimeline` in `steps.ts`). A turn without steps,
 * the summary or a question, has the thread's in-progress line instead, also
 * while it waits in the queue, so `queued`, `starting…` and a step-less
 * `stopping…` belong to plot runs.
 */

import Box from '@mui/material/Box';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import type { RunState } from 'src/hooks/useAgentSession';
import { RoundGrid } from 'src/sections/agent-chat/RoundGrid';
import { liveRows } from 'src/sections/agent-chat/timeline';
import { fontSize, typography } from 'src/theme';

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
    // The site's loader stands beside the run for as long as it lasts, centred on its first line
    // (the queue line or the grid's first row); on a phone above it, so the grid keeps the full
    // width. Both columns take the run's font from here, so the loader's box is one line of it.
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        alignItems: 'flex-start',
        gap: { xs: 1, sm: 1.5 },
        fontFamily: typography.mono,
        fontSize: fontSize.md,
      }}
    >
      <Box
        component="span"
        sx={{
          display: 'flex',
          alignItems: 'center',
          // A zero-width character makes the box one text line of the run's font, as tall as the
          // line beside it, and the loader centres on it the way the step dots centre in theirs.
          '&::before': { content: '"\\200b"' },
        }}
      >
        <LoaderSpinner size="inline" />
      </Box>
      <Box aria-live="polite" sx={{ display: 'grid', gap: 0.75, minWidth: 0 }}>
        {before && !(stopping && !waiting) && <Box sx={{ color: 'var(--ink)' }}>{before}</Box>}
        {rows.length > 0 && <RoundGrid rows={rows} label="Progress" />}
        {stopping && <Box sx={{ color: 'var(--ink-muted)' }}>{stopping}</Box>}
      </Box>
    </Box>
  );
}
