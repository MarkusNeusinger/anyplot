/**
 * The one working line at the thread's foot (the v4 design), for every turn and both lanes: the
 * site's inline loader (`LoaderSpinner`, kit 6 option A) beside what the turn does now
 * (`workingLine` in `steps.ts`): `drawing your plot · second try · 0:42`, `waiting · you are 3rd`,
 * `summarizing your data`, `writing the reply` below a run's card, the stop and the reconnect.
 * On a phone a plot reads `drawing · 0:42`, and from the second try on `drawing · second try ·
 * 0:42`, the try kept. It took the place of the thread's in-progress line, of
 * the progress timeline below the thread, whose grid is the admin menu's now, and of the queue
 * counter. The first reply takes its place without a jump: it stands in the reply's slot, in the
 * reply's line height.
 *
 * It stands inside the thread's log, whose polite live region reads it as it comes and each change
 * of its words (a second try, a stop); the clock beside the words is hidden from it (`RunClock`).
 * While a plot is drawn the page's scroll anchoring is off, as it was while the progress grid
 * stood below the thread: what the run sends in waits (`runView`), and a browser holding a node
 * below in place would only scroll the page under the line.
 */

import { useEffect } from 'react';

import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import { RunClock } from 'src/sections/agent-chat/RunClock';
import { holdScrollAnchoring } from 'src/sections/agent-chat/scrollAnchoring';
import type { WorkingLineText } from 'src/sections/agent-chat/steps';
import { bodyTextSx, PHONE_QUERY } from 'src/sections/agent-chat/styles';
import { fontSize, typography } from 'src/theme';

/** The page's scroll anchoring off while it is mounted (`holdScrollAnchoring`). */
function NoScrollAnchoring() {
  useEffect(() => holdScrollAnchoring(), []);
  return null;
}

export interface WorkingLineProps {
  line: WorkingLineText;
  /** A plot is drawn (`runView`): the page's scroll anchoring stays off meanwhile. */
  drawing: boolean;
}

export function WorkingLine({ line, drawing }: WorkingLineProps) {
  // Read at the first render, so a phone never shows the long words first.
  const narrow = useMediaQuery(PHONE_QUERY, { noSsr: true });
  return (
    <Box
      data-testid="working-line"
      data-kind={line.kind}
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 1.5,
        fontFamily: typography.mono,
        fontSize: fontSize.md,
        lineHeight: bodyTextSx.lineHeight,
        color: 'var(--ink-soft)',
      }}
    >
      {drawing && <NoScrollAnchoring />}
      {/* A zero-width character makes the loader's box one text line tall, so the loader centres
          on the words' first line. */}
      <Box
        component="span"
        sx={{ display: 'flex', alignItems: 'center', '&::before': { content: '"\\200b"' } }}
      >
        <LoaderSpinner size="inline" />
      </Box>
      <Box sx={{ minWidth: 0 }}>
        {narrow ? line.short : line.text}
        {line.clockFrom !== null && <RunClock from={line.clockFrom} prefix=" · " />}
      </Box>
    </Box>
  );
}
