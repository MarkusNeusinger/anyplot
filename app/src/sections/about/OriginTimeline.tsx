import Box from '@mui/material/Box';

import { ORIGIN_EVENTS } from 'src/sections/about/figureData';
import {
  DATE_SIZE,
  layoutTimeline,
  TIMELINE_MIN_WIDTH,
  WHAT_SIZE,
} from 'src/sections/about/timelineLayout';
import { typography } from 'src/theme';

const drawn = `@container (min-width: ${TIMELINE_MIN_WIDTH}px)` as const;

// Vertical measures of the drawn form: a label of two lines is about 31px tall, the rows of one
// side 38px apart; labels above the axis stand off it by 34px, labels below by 12px.
const LABEL_HEIGHT = 31;
const ROW_STEP = 38;
const UP_GAP = 34;
const DOWN_GAP = 12;
const DOT = 7;

export interface OriginTimelineProps {
  /** The day "today" stands at; the axis runs from the first point to it. */
  now?: Date;
}

/**
 * The origin as a timeline: an ordered list of its points, from the start as pyplots.ai to today.
 * From a column of 720px it is drawn to scale on an axis, labels above and below it; narrower, it
 * is a list down a rule, like a git log. Dots, leaders and the axis are drawn for the eye; the
 * list's text carries every date and what happened on it.
 */
export function OriginTimeline({ now = new Date() }: OriginTimelineProps) {
  const points = layoutTimeline(ORIGIN_EVENTS, now);
  const levels = (side: 'up' | 'down') =>
    Math.max(1, ...points.filter(p => p.side === side).map(p => p.level));
  const axisY = 4 + LABEL_HEIGHT + UP_GAP + (levels('up') - 1) * ROW_STEP;
  const height = axisY + DOWN_GAP + LABEL_HEIGHT + 4 + (levels('down') - 1) * ROW_STEP;

  return (
    <Box sx={{ containerType: 'inline-size', mt: 3.5, mb: 1 }}>
      <Box
        component="ol"
        sx={{
          listStyle: 'none',
          m: 0,
          ml: '4px',
          p: 0,
          pl: 2,
          borderLeft: '1px solid var(--ink-muted)',
          display: 'grid',
          rowGap: 1.25,
          fontFamily: typography.mono,
          [drawn]: {
            position: 'relative',
            display: 'block',
            height,
            ml: 0,
            pl: 0,
            borderLeft: 0,
            '&::before': {
              content: '""',
              position: 'absolute',
              left: 0,
              right: 0,
              top: axisY,
              borderTop: '1px solid var(--ink-muted)',
            },
          },
        }}
      >
        {points.map(point => {
          const offset = (point.level - 1) * ROW_STEP;
          const up = point.side === 'up';
          return (
            <Box
              component="li"
              key={point.key}
              sx={{
                position: 'relative',
                lineHeight: 1.35,
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  left: -20.5,
                  top: 5,
                  width: DOT,
                  height: DOT,
                  boxSizing: 'border-box',
                  borderRadius: '50%',
                  border: '1px solid var(--ink-soft)',
                  bgcolor: point.today ? 'var(--bg-page)' : 'var(--ink-soft)',
                },
                [drawn]: {
                  position: 'absolute',
                  top: 0,
                  left: `${point.percent}%`,
                  width: 0,
                  height,
                  '&::before': { left: -DOT / 2, top: axisY - DOT / 2 },
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    left: 0,
                    top: up ? axisY - UP_GAP + 4 - offset : axisY + 4,
                    height: up ? UP_GAP - 10 + offset : DOWN_GAP - 6 + offset,
                    borderLeft: '1px solid var(--rule)',
                  },
                },
              }}
            >
              <Box
                sx={{
                  [drawn]: {
                    position: 'absolute',
                    whiteSpace: 'nowrap',
                    ...(up
                      ? { bottom: height - axisY + UP_GAP + offset }
                      : { top: axisY + DOWN_GAP + offset }),
                    ...(point.align === 'start' ? { left: 0 } : { right: 0, textAlign: 'right' }),
                  },
                }}
              >
                {point.date && (
                  <>
                    <Box
                      component="time"
                      dateTime={point.dateTime}
                      sx={{ display: 'block', fontSize: DATE_SIZE, color: 'var(--ink-muted)' }}
                    >
                      {point.date}
                    </Box>{' '}
                  </>
                )}
                <Box
                  component="span"
                  sx={{ display: 'block', fontSize: WHAT_SIZE, color: 'var(--ink-soft)' }}
                >
                  {point.what}
                </Box>
              </Box>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
