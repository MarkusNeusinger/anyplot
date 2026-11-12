/**
 * One bar per UTC day, with the first and the last date under it: the strip of the stats page's
 * machine readers and shared links tiles, drawn like the visitors strip above them
 * (`stripGeometry.ts`).
 *
 * One series, so one colour and no legend: the tile's title says what a bar is. A bar's height
 * alone encodes the day's number (`columnPx`). Each day's full-height column is its own hover and
 * keyboard-focus target, named with the date and the number, so a short bar is as easy to reach
 * as a tall one. A day without anything draws the floor in muted ink: "none", not a gap in the
 * data.
 */

import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { CHART_PX, columnPx, STRIP_BAR } from 'src/sections/stats/stripGeometry';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface DayStripDay {
  date: string;
  value: number;
}

export interface DayStripProps {
  /** The window's days, oldest first. */
  days: DayStripDay[];
  /** The strip's name for assistive technology, such as "shared links per day". */
  label: string;
  /** A day's number in words, such as `4 shares`; it follows the date in the column's name. */
  describe: (value: number) => string;
  /** The prefix of the test ids: `<testId>-day` on a column, `<testId>-bar` on its bar. */
  testId: string;
}

const dateSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.micro,
  color: semanticColors.mutedText,
} as const;

export function DayStrip({ days, label, describe, testId }: DayStripProps) {
  const busiest = Math.max(...days.map(day => day.value), 1);

  return (
    <>
      <Box
        role="group"
        aria-label={label}
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 0.25,
          height: CHART_PX,
          overflow: 'hidden',
        }}
      >
        {days.map(day => (
          <Tooltip key={day.date} title={`${day.date}: ${describe(day.value)}`} arrow>
            {/* Focusable, so a keyboard reaches each day's number as a pointer does; the
                Tooltip names the column (`aria-label`), which `role="img"` lets assistive
                technology read. */}
            <Box
              data-testid={`${testId}-day`}
              role="img"
              tabIndex={0}
              sx={{
                flex: 1,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-end',
                borderRadius: '2px 2px 0 0',
                outline: 'none',
                '&:hover, &:focus-visible': { bgcolor: 'var(--rule)' },
                '&:focus-visible': { boxShadow: `inset 0 -2px 0 ${colors.primary}` },
                '&:hover .day-strip-bar, &:focus-visible .day-strip-bar': {
                  opacity: STRIP_BAR.activeOpacity,
                },
                transition: 'background-color 0.15s ease',
              }}
            >
              <Box
                data-testid={`${testId}-bar`}
                className={day.value > 0 ? 'day-strip-bar' : undefined}
                sx={{
                  height: `${columnPx(day.value, busiest)}px`,
                  flexShrink: 0,
                  borderRadius: '2px 2px 0 0',
                  transition: 'opacity 0.15s ease',
                  ...(day.value > 0
                    ? { bgcolor: STRIP_BAR.color, opacity: STRIP_BAR.opacity }
                    : { bgcolor: semanticColors.mutedText, opacity: 0.35 }),
                }}
              />
            </Box>
          </Tooltip>
        ))}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
        <Typography sx={dateSx}>{days[0]?.date}</Typography>
        <Typography sx={dateSx}>{days[days.length - 1]?.date}</Typography>
      </Box>
    </>
  );
}
