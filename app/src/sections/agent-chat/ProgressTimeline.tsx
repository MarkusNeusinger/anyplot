/**
 * The progress grid of the running turn, from its `status` events, in the admin menu (owner,
 * 2026-11-06: every admin extra behind the one admin element; visitors and admins see the same
 * working line at the thread's foot). The rounds of the pipeline as a grid (`RoundGrid`,
 * `timeline.ts`): one row per round with its steps in fixed columns, the active step marked, the
 * steps still to come muted, and a finished round's outcome on the right (from the repair step's
 * `outcome`). Before the first step, the first try's outcome cell says where the run stands:
 * `starting…`, or the wait in the run queue with the position.
 *
 * The page passes it to the admin menu while a run is set, for a plot run from the queue on and
 * for any turn that reached a pipeline step; a turn without steps has no rows, so the section
 * says so. The menu's popover stays mounted while closed, so this mounts with every run: it holds
 * no scroll anchoring and no loader of its own. The working line holds both (`WorkingLine.tsx`),
 * and it also says that the run stops or reconnects.
 */

import Box from '@mui/material/Box';

import type { RunState } from 'src/hooks/useAgentSession';
import { RoundGrid } from 'src/sections/agent-chat/RoundGrid';
import { labelSx } from 'src/sections/agent-chat/styles';
import { liveRows } from 'src/sections/agent-chat/timeline';

export function ProgressTimeline({ run }: { run: RunState }) {
  const rows = liveRows(run);
  const waiting = run.steps[run.steps.length - 1]?.step === 'queued';
  const started = run.steps.some(entry => entry.step !== 'queued');
  // Before the first pipeline step: the queue position, or that the run is starting.
  const status = waiting
    ? run.queue
      ? `queued · ${run.queue.position} of ${run.queue.waiting}`
      : 'queued'
    : started
      ? null
      : 'starting…';
  return (
    <Box data-testid="progress-grid" sx={{ minWidth: 0, overflowX: 'auto' }}>
      {rows.length > 0 ? (
        <RoundGrid rows={rows} label="Progress" status={status} />
      ) : (
        // A turn without pipeline steps (the summary, a question) has no grid: its words are the
        // working line's.
        <Box sx={labelSx}>no pipeline step yet</Box>
      )}
    </Box>
  );
}
