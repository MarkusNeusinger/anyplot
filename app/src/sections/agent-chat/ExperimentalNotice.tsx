/**
 * The public lane's notice above the first input, one line since 2026-11-02 (owner: less
 * text, the details behind a button rather than removed). The line keeps in view, without a
 * click, that this is an experimental AI (the EU AI Act's Art. 50 duty to say that a person
 * talks to an AI), that its results can be wrong, and that nothing is stored without feedback.
 * The ⓘ button at its end opens the rest: which AI and where it runs, what not to paste, the
 * daily limits, and the legal page's section on the assistant.
 *
 * A popover rather than a tooltip: it opens on a tap as on a click, it holds a link, and it
 * keeps the keyboard focus inside until Escape or a click outside closes it, which returns the
 * focus to the button. The link opens a new tab: leaving the page would end the session. The
 * texts live in `lane.ts`, with the public lane's consent line.
 */

import { useId, useState } from 'react';

import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';

import { paths } from 'src/routes/paths';
import { EXPERIMENTAL_DETAILS, EXPERIMENTAL_LINE } from 'src/sections/agent-chat/lane';
import { labelSx } from 'src/sections/agent-chat/styles';
import { colors, proseLinkStyle } from 'src/theme';

/**
 * The ⓘ button: 32 px to tap, which the negative margin keeps out of the line height, so the
 * line it ends reads as text.
 */
const infoButtonSx = {
  p: 0.75,
  my: -0.75,
  ml: 0.25,
  color: 'var(--ink-soft)',
  '&:hover': { color: colors.primary, bgcolor: 'var(--bg-elevated)' },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
} as const;

export function ExperimentalNotice() {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const popoverId = useId();
  const open = anchor !== null;
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
        <IconButton
          size="small"
          aria-label="About the assistant"
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls={open ? popoverId : undefined}
          onClick={(event: React.MouseEvent<HTMLElement>) => setAnchor(event.currentTarget)}
          sx={infoButtonSx}
        >
          <InfoOutlinedIcon sx={{ fontSize: 18 }} />
        </IconButton>
      </Box>
      <Popover
        id={popoverId}
        open={open}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{
          paper: {
            role: 'dialog',
            'aria-label': 'About the assistant',
            sx: { width: { xs: 'calc(100vw - 32px)', sm: 380 }, p: 1.5, mt: 0.5 },
          },
        }}
      >
        <Box sx={{ ...labelSx, mb: 0.75 }}># about the assistant</Box>
        <Box
          component="ul"
          data-testid="experimental-details"
          sx={{
            ...labelSx,
            color: 'var(--ink)',
            lineHeight: 1.6,
            m: 0,
            pl: 0,
            listStyle: 'none',
            display: 'flex',
            flexDirection: 'column',
            gap: 0.25,
          }}
        >
          {EXPERIMENTAL_DETAILS.map(line => (
            <li key={line}>{line}</li>
          ))}
          <li>
            <Box
              component="a"
              href={`${paths.legal}#assistant`}
              target="_blank"
              rel="noopener"
              sx={proseLinkStyle}
            >
              how the assistant works
            </Box>
          </li>
        </Box>
      </Popover>
    </Box>
  );
}
