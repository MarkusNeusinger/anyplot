/**
 * The site's loader: three dots, the last tweening between imprint green and ochre over a 2 s
 * loop. `large` and `small` stand alone (the plots gallery); `inline` (40 x 8 px) sits in a line
 * of text, as the agent chat's working lines do.
 *
 * Decorative: hidden from screen readers, whose live regions say what is loading. The box is
 * fixed, so a line never moves when the loader comes or goes. Under `prefers-reduced-motion`
 * the dots stand still. Each size has keyframes of its own (`trfLoader-inline`): emotion writes
 * an `@keyframes` block under its literal name, and two sizes on one page would otherwise share
 * whichever block came last, with the other size's offsets.
 */

import Box from '@mui/material/Box';

import { colors } from 'src/theme';

export type LoaderSize = 'large' | 'small' | 'inline';

/** Width of the box, the dot's size and the second dot's offset per size; the third is at twice that. */
const GEOMETRY: Record<LoaderSize, { width: number; dot: number; offset: number }> = {
  large: { width: 100, dot: 16, offset: 32 },
  small: { width: 75, dot: 12, offset: 24 },
  inline: { width: 40, dot: 8, offset: 16 },
};

interface LoaderSpinnerProps {
  size?: LoaderSize;
}

export function LoaderSpinner({ size = 'large' }: LoaderSpinnerProps) {
  const { width, dot, offset } = GEOMETRY[size];
  const doubleOffset = offset * 2;
  const tween = `trfLoader-${size}`;
  const move = `ballMoveX-${size}`;
  const inline = size === 'inline';

  return (
    <Box
      // A span inline, so the loader may stand inside a line's own span or paragraph.
      component={inline ? 'span' : 'div'}
      aria-hidden
      data-testid="loader-spinner"
      data-size={size}
      sx={{
        position: 'relative',
        ...(inline && { display: 'inline-block', verticalAlign: 'middle' }),
        flexShrink: 0,
        width,
        height: dot,
        '&::before': {
          content: '""',
          position: 'absolute',
          width: dot,
          height: dot,
          borderRadius: '50%',
          background: colors.primary,
          boxShadow: `${offset}px 0 ${colors.primary}`,
          left: 0,
          top: 0,
          animation: `${move} 2s linear infinite`,
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          width: dot,
          height: dot,
          borderRadius: '50%',
          background: colors.primary,
          left: 0,
          top: 0,
          transform: `translateX(${doubleOffset}px) scale(1)`,
          zIndex: 2,
          animation: `${tween} 2s linear infinite`,
        },
        [`@keyframes ${tween}`]: {
          '0%, 5%': {
            transform: `translateX(${doubleOffset}px) scale(1)`,
            background: colors.primary,
          },
          '10%': {
            transform: `translateX(${doubleOffset}px) scale(1)`,
            background: colors.accent,
          },
          '40%': {
            transform: `translateX(${offset}px) scale(1.5)`,
            background: colors.accent,
          },
          '90%, 95%': {
            transform: 'translateX(0px) scale(1)',
            background: colors.accent,
          },
          '100%': {
            transform: 'translateX(0px) scale(1)',
            background: colors.primary,
          },
        },
        [`@keyframes ${move}`]: {
          '0%, 10%': { transform: 'translateX(0)' },
          '90%, 100%': { transform: `translateX(${offset}px)` },
        },
        // Three dots at rest: the pair of `::before` and the third of `::after` where the loop starts.
        '@media (prefers-reduced-motion: reduce)': {
          '&::before, &::after': { animation: 'none' },
        },
      }}
    />
  );
}
