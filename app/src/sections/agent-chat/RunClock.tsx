/**
 * The run's clock, `0:42`: the time since `from` (`RunState.startedAt`), in the working line at
 * the thread's foot and in the status line at the frame's foot. It ticks once a second in this
 * leaf alone, so the page around it never renders every second. Every tick reads
 * `Date.now() - from` afresh and never counts ticks: a background tab throttles its timers, and
 * the clock reads right again at its next tick.
 *
 * Hidden from screen readers (PLAN §4): the thread's log and the status line's live region read
 * text changes, and a time read out every second is noise; the step and the try are words they
 * do read. The plot button's description, the status line, leaves it out for the same reason.
 */

import { useEffect, useState } from 'react';

import Box from '@mui/material/Box';

import { elapsedClock } from 'src/sections/agent-chat/messages';

/** One second: the clock's resolution. */
export const CLOCK_TICK_MS = 1000;

export function RunClock({ from, prefix = '' }: { from: number; prefix?: string }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), CLOCK_TICK_MS);
    return () => window.clearInterval(timer);
  }, []);
  return (
    <Box component="span" aria-hidden data-testid="run-clock">
      {prefix}
      {elapsedClock(now - from)}
    </Box>
  );
}
