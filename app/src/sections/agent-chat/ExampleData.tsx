/**
 * The chat's way to data without a file: a line above the composer while the session has no
 * data, `# no data at hand?  .example_data()`, which asks the assistant for example data to try
 * the plot. It sends the turn action `example_data`, never typed words: the session's first
 * typed message sets the session language, so typed English would keep a German visitor in
 * English.
 *
 * While that turn runs and no data has arrived, the line steps aside: the thread's in-progress
 * line says "making example data" beside the site's loader, once, where the reply will come.
 */

import Box from '@mui/material/Box';

import { actionButtonSx, labelSx } from 'src/sections/agent-chat/styles';

/** The line's words; the owner reads every user-facing text in the PR's "Texts to read". */
export const EXAMPLE_DATA_PROMPT = '# no data at hand?';

export interface ExampleDataLineProps {
  /** The `example_data` turn runs and no data has arrived yet: the line shows nothing. */
  working: boolean;
  /** Something else is in flight, or the session is not ready. */
  disabled: boolean;
  onClick: (event: React.MouseEvent) => void;
}

export function ExampleDataLine({ working, disabled, onClick }: ExampleDataLineProps) {
  if (working) return null;
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
        mb: -1,
      }}
    >
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
    </Box>
  );
}
