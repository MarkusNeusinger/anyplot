/**
 * The chat's notice, on both lanes since 2026-11-06 (the admin's chat is the visitors'), one
 * muted line above the chat's frame since the v4 frame of 2026-11-06, right-aligned from `sm`
 * up and at the left at phone width:
 * `// experimental AI · answers can be wrong ⓘ` (a `#` line with a green rule inside the chat
 * until then; one line since 2026-11-02, owner: less text, the details behind a button rather
 * than removed). It stands above the first input whatever the session's state. The line keeps
 * in view, without a
 * click, that this is an experimental AI (the EU AI Act's Art. 50 duty to say that a person
 * talks to an AI) and that its answers can be wrong. The ⓘ button at its end (`InfoPopover`)
 * opens the rest: where the chat and the data live and for how long, that nothing is saved
 * without feedback, which AI it is, where it runs and that it does not train on them, what not
 * to paste, the daily limits, and the legal page's section on the assistant. The link opens a
 * new tab: leaving the page would end the session. The texts live in `lane.ts`, with the
 * feedback form's consent line.
 */

import Box from '@mui/material/Box';

import { paths } from 'src/routes/paths';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { EXPERIMENTAL_DETAILS, EXPERIMENTAL_LINE } from 'src/sections/agent-chat/lane';
import { labelSx } from 'src/sections/agent-chat/styles';
import { proseLinkStyle } from 'src/theme';

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
        // Muted in words, not in contrast: the soft ink reads 4.5:1 and more in both themes.
        color: 'var(--ink-soft)',
        textAlign: { xs: 'left', sm: 'right' },
        lineHeight: 1.6,
        mb: 0.5,
      }}
    >
      {'// '}
      {words.join(' ')}{' '}
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
