/**
 * The progress of the running turn, from its `status` events: the rounds of the
 * pipeline as a grid (`RoundGrid`, `timeline.ts`): one row per round with its
 * steps in fixed columns, the active step marked, the steps still to come muted,
 * and a finished round's outcome on the right (from the repair step's
 * `outcome`). Before the first step, the first try's outcome cell says where the
 * run stands: `starting…`, or the wait in the run queue with the position. The
 * site's loader stands beside it while the run lasts, also while it stops.
 *
 * From the click to the result card nothing above the grid's first row comes or
 * goes, so the loader and the grid stand still while the steps advance (a
 * `starting…` line above the grid used to go away at the first step, and the
 * grid jumped up one line beside the loader). A stop adds its line below the grid,
 * and so does a cut stream while the page reads the rest of the turn again.
 * While it is mounted the page has no scroll anchoring: a repair round's row
 * grows the grid downwards, and the browser, holding a node below it in place,
 * scrolled the page by that row, so the loader and the rows already shown
 * jumped up by it (25 px at desktop width, 65 px at phone width).
 *
 * The page mounts it for a plot run, from the queue on, and for any turn that
 * reached a pipeline step (`showsTimeline` in `steps.ts`). A turn without steps,
 * the summary or a question, has the thread's in-progress line instead, also
 * while it waits in the queue, so `queued`, `starting…` and a step-less
 * `stopping…` belong to plot runs.
 */

import { useEffect } from 'react';

import Box from '@mui/material/Box';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import type { RunState } from 'src/hooks/useAgentSession';
import { RECONNECTING_TEXT } from 'src/sections/agent-chat/messages';
import { RoundGrid } from 'src/sections/agent-chat/RoundGrid';
import { holdScrollAnchoring } from 'src/sections/agent-chat/scrollAnchoring';
import { liveRows } from 'src/sections/agent-chat/timeline';
import { fontSize, typography } from 'src/theme';

/**
 * Turns the page's scroll anchoring off while the run lasts (`holdScrollAnchoring`). The run's
 * grid grows only below what it shows, so the anchoring has nothing to hold still there and would
 * only scroll the page by each new row; the page's value comes back when the last hold ends.
 * Excluding the composer or the footer alone did not stop the jump: the browser found another
 * anchor.
 */
function useNoScrollAnchoring() {
  useEffect(() => holdScrollAnchoring(), []);
}

export function ProgressTimeline({ run }: { run: RunState }) {
  useNoScrollAnchoring();
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
  // The stream was cut and the page reads the rest of the turn: quiet, since the run goes on.
  const reconnecting = run.reconnecting && !stopping ? RECONNECTING_TEXT : null;
  // A stop before the run started replaces `starting…`; one in the queue keeps the position.
  const status = before && !(stopping && !waiting) ? before : null;

  return (
    // The site's loader stands beside the run for as long as it lasts, centred on its first line
    // (the grid's first row); on a phone above it, so the grid keeps the full width. Both columns
    // take the run's font from here, so the loader's box is one line of it.
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
        {rows.length > 0 ? (
          <RoundGrid rows={rows} label="Progress" status={status} />
        ) : (
          // A turn without a grid yet (the page shows its in-progress line instead): the line alone.
          status && <Box sx={{ color: 'var(--ink)' }}>{status}</Box>
        )}
        {stopping && <Box sx={{ color: 'var(--ink-muted)' }}>{stopping}</Box>}
        {reconnecting && <Box sx={{ color: 'var(--ink-muted)' }}>{reconnecting}</Box>}
      </Box>
    </Box>
  );
}
