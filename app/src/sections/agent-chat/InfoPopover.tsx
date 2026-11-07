/**
 * The ⓘ button at the end of a one-line header of the chat, and the popover it opens with the
 * details that would otherwise crowd the line (owner, 2026-11-02: less text, the details behind
 * buttons rather than removed). The experimental notice (`ExperimentalNotice`), the data card's
 * `# your data` header (`DataCard`), the thread's reply-language line (`ChatThread`), the
 * remembered list's heading (`Remembered`), a result card's notes (`ResultCard`, the review's
 * lines in full) and the thread's start item (`StartItem`: the columns the plot expects, after
 * the chips, and the how-to of the data) use it.
 *
 * A popover rather than a tooltip: it opens on a tap as on a click, it can hold a link, and it
 * keeps the keyboard focus inside until Escape or a click outside closes it, which returns the
 * focus to the button.
 */

import { type ReactNode, useId, useState } from 'react';

import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';

import { labelSx } from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

export interface InfoPopoverProps {
  /** The button's and the popover's accessible name, in words: "About the assistant". */
  label: string;
  /** The popover's first line, a `#` comment. */
  heading: string;
  /** The popover's lines, one list item each. */
  lines: readonly ReactNode[];
  /** The list's test id. */
  testId?: string;
}

export function InfoPopover({ label, heading, lines, testId }: InfoPopoverProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const popoverId = useId();
  const open = anchor !== null;

  return (
    <>
      <IconButton
        size="small"
        aria-label={label}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? popoverId : undefined}
        onClick={(event: React.MouseEvent<HTMLElement>) => setAnchor(event.currentTarget)}
        sx={{
          // 32 px to tap; the negative margin keeps it out of the line height, so the line it
          // ends reads as text.
          p: 0.75,
          my: -0.75,
          ml: 0.25,
          color: 'var(--ink-soft)',
          '&:hover': { color: colors.primary, bgcolor: 'var(--bg-elevated)' },
          '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
        }}
      >
        <InfoOutlinedIcon sx={{ fontSize: 18 }} />
      </IconButton>
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
            'aria-label': label,
            sx: { width: { xs: 'calc(100vw - 32px)', sm: 420 }, p: 1.5, mt: 0.5 },
          },
        }}
      >
        <Box sx={{ ...labelSx, mb: 0.75 }}>{heading}</Box>
        <Box
          component="ul"
          data-testid={testId}
          sx={{
            ...labelSx,
            color: 'var(--ink)',
            lineHeight: 1.6,
            m: 0,
            pl: 0,
            listStyle: 'none',
            display: 'flex',
            flexDirection: 'column',
            // A line that wraps at phone width still reads as one item.
            gap: 0.75,
          }}
        >
          {lines.map((line, index) => (
            <li key={index}>{line}</li>
          ))}
        </Box>
      </Popover>
    </>
  );
}
