/**
 * The public lane's notice above the first input, one line since 2026-11-02 (owner: less
 * text, the details behind a button rather than removed). The line keeps in view, without a
 * click, that this is an experimental AI (the EU AI Act's Art. 50 duty to say that a person
 * talks to an AI), that its results can be wrong, and that nothing is stored without feedback.
 * The ⓘ button at its end (`InfoPopover`) opens the rest: which AI and where it runs, what not
 * to paste, the daily limits, and the legal page's section on the assistant. The link opens a
 * new tab: leaving the page would end the session. The texts live in `lane.ts`, with the
 * public lane's consent line.
 */

import Box from '@mui/material/Box';

import { paths } from 'src/routes/paths';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { EXPERIMENTAL_DETAILS, EXPERIMENTAL_LINE } from 'src/sections/agent-chat/lane';
import { labelSx } from 'src/sections/agent-chat/styles';
import { colors, proseLinkStyle } from 'src/theme';

export function ExperimentalNotice() {
  // The last word and the button keep together, so the ⓘ never wraps onto a line of its own.
  const words = EXPERIMENTAL_LINE.split(' ');
  const last = words.pop();

  return (
    <Box
      role="note"
      data-testid="experimental-notice"
      sx={{
        ...labelSx,
        color: 'var(--ink)',
        borderLeft: `3px solid ${colors.primary}`,
        pl: 1.5,
        mb: 2,
        lineHeight: 1.6,
      }}
    >
      # {words.join(' ')}{' '}
      <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
        {last}
        <InfoPopover
          label="About the assistant"
          heading="# about the assistant"
          testId="experimental-details"
          lines={[
            ...EXPERIMENTAL_DETAILS,
            <Box
              key="legal"
              component="a"
              href={`${paths.legal}#assistant`}
              target="_blank"
              rel="noopener"
              sx={proseLinkStyle}
            >
              how the assistant works
            </Box>,
          ]}
        />
      </Box>
    </Box>
  );
}
