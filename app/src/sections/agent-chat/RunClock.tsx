/**
 * The run's clock, `0:42`: the time since `from` (`RunState.startedAt`), in the working line at
 * the thread's foot and in the status line at the frame's foot. It ticks once a second in this
 * leaf alone, so the page around it never renders every second. Every tick reads
 * `Date.now() - from` afresh and never counts ticks: a background tab throttles its timers, and
 * the clock reads right again at its next tick. Each tick lands on a whole second of the elapsed
 * time, so the working line's clock and the status line's, which count from the same start,
 * turn over together and never show two times at once.
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

/** How long until the elapsed time since `from` reaches its next whole second. */
function untilNextSecond(from: number, now: number): number {
  const into = (((now - from) % CLOCK_TICK_MS) + CLOCK_TICK_MS) % CLOCK_TICK_MS;
  return CLOCK_TICK_MS - into;
}

export function RunClock({ from, prefix = '' }: { from: number; prefix?: string }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    let timer = 0;
    const tick = () => {
      const current = Date.now();
      setNow(current);
      timer = window.setTimeout(tick, untilNextSecond(from, current));
    };
    timer = window.setTimeout(tick, untilNextSecond(from, Date.now()));
    return () => window.clearTimeout(timer);
  }, [from]);
  return (
    <Box component="span" aria-hidden data-testid="run-clock">
      {prefix}
      {elapsedClock(now - from)}
    </Box>
  );
}
