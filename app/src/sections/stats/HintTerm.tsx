/**
 * A word of a stats tile's line with a hint: a button that reads as the line's own text, dotted
 * like a term with a note. The hint describes the word and leaves its name alone
 * (`describeChild`).
 *
 * - A pointer and a keyboard open the hint the tooltip's own way.
 * - A tap opens it through the click. The tooltip's touch timer runs between the finger's
 *   down and up, so it opens for a long press and misses a tap.
 * - It closes when the pointer or the focus leaves, on Escape, and some seconds after a touch:
 *   long enough to read two sentences, where the default is 1.5 s.
 * - It opens under the word, so the line above stays readable beside it.
 */

import { type ReactNode, useState } from 'react';

import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';

import { colors } from 'src/theme';

const hintTermSx = {
  font: 'inherit',
  letterSpacing: 'inherit',
  color: 'inherit',
  background: 'none',
  border: 0,
  p: 0,
  m: 0,
  textDecoration: 'underline dotted',
  textUnderlineOffset: '3px',
  cursor: 'help',
  '&:focus-visible': {
    outline: `2px solid ${colors.primary}`,
    outlineOffset: 2,
    borderRadius: '2px',
  },
} as const;

export interface HintTermProps {
  /** What the word carries as its description. */
  hint: string;
  testId: string;
  /** The word itself. */
  children: ReactNode;
}

export function HintTerm({ hint, testId, children }: HintTermProps) {
  const [open, setOpen] = useState(false);
  return (
    <Tooltip
      title={hint}
      arrow
      describeChild
      placement="bottom-start"
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      leaveTouchDelay={8000}
    >
      <Box
        component="button"
        type="button"
        data-testid={testId}
        onClick={() => setOpen(true)}
        sx={hintTermSx}
      >
        {children}
      </Box>
    </Tooltip>
  );
}
