/**
 * The chat's way to data without a file: a line above the composer while the session has no
 * data, `# no data at hand?  .example_data()`, which asks the assistant for example data to try
 * the plot. It sends the turn action `example_data`, never typed words: the session's first
 * typed message sets the session language, so typed English would keep a German visitor in
 * English.
 *
 * While that turn runs and no data has arrived, the line says so instead, pulses its `…` and
 * counts the seconds from the second one on, as the data box does for a parse (`BoxWorking`): a
 * plain indicator, no spinner (docs/reference/style-guide.md §10.1). Screen readers hear the
 * thread's in-progress line, which says the same once, so this one is hidden from them.
 */

import { useEffect, useState } from 'react';

import Box from '@mui/material/Box';

import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { actionButtonSx, labelSx } from 'src/sections/agent-chat/styles';

/** The line's words; the owner reads every user-facing text in the PR's "Texts to read". */
export const EXAMPLE_DATA_PROMPT = '# no data at hand?';
export const EXAMPLE_DATA_WORKING = '# making example data';

function Working() {
  const [start] = useState(() => Date.now());
  const [now, setNow] = useState(start);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  const seconds = Math.max(0, Math.floor((now - start) / 1000));

  return (
    <Box
      component="span"
      aria-hidden
      data-testid="example-data-working"
      sx={{ color: 'var(--ink-soft)' }}
    >
      {EXAMPLE_DATA_WORKING} <Ellipsis />
      {seconds >= 1 ? ` · ${seconds} s` : ''}
    </Box>
  );
}

export interface ExampleDataLineProps {
  /** The `example_data` turn runs and no data has arrived yet. */
  working: boolean;
  /** Something else is in flight, or the session is not ready. */
  disabled: boolean;
  onClick: (event: React.MouseEvent) => void;
}

export function ExampleDataLine({ working, disabled, onClick }: ExampleDataLineProps) {
  return (
    <Box
      data-testid="example-data"
      sx={{
        ...labelSx,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        // The button's own padding is most of the gap: the two read as one line.
        columnGap: 0.25,
        // The button's height, so the working line takes its place without a jump.
        minHeight: 32,
        mb: -1,
      }}
    >
      {working ? (
        <Working />
      ) : (
        <>
          <Box component="span">{EXAMPLE_DATA_PROMPT}</Box>
          <Box
            component="button"
            type="button"
            onClick={onClick}
            disabled={disabled}
            aria-label="Make example data"
            sx={{ ...actionButtonSx, color: 'var(--ink)' }}
          >
            .example_data()
          </Box>
        </>
      )}
    </Box>
  );
}
