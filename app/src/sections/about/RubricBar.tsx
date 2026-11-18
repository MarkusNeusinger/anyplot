import { useId } from 'react';

import Box from '@mui/material/Box';

import { RUBRIC_CAPTION, RUBRIC_PARTS } from 'src/sections/about/figureData';
import { monoWidth } from 'src/sections/about/monoWidth';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import { typography } from 'src/theme';

const NAME_SIZE = 12;
const PAD_LEFT = 10;
const PAD_RIGHT = 8;

// Under the bar each name stands beneath its part. The narrowest, a 10-point part, has to hold
// "quality" or "mastery" at 12px (56px where advances are rounded to whole pixels, 53.8px where
// they are not) with its 18px of padding: 74px, which is 10 % of 740px. Narrower, the names leave
// the bar for a list of two columns under it, each with its points.
const UNDER_MIN_WIDTH = (monoWidth('mastery', NAME_SIZE) + PAD_LEFT + PAD_RIGHT) * 10;
const under = `@container (min-width: ${UNDER_MIN_WIDTH}px)` as const;

const SEGMENT_GAP = '2px solid var(--bg-page)';
const SEGMENT_GAP_WIDTH = 2;
const POINTS_SIZE = 14;
const SEGMENT_PAD = 8;
const SEGMENT_PAD_TIGHT = 4;

// In the bar the narrowest part, 10 points, holds its "10" (18px) with the full padding only from
// this width on (360px). Narrower, which is every phone up to 390px wide, the padding gives way
// first, so the number stays inside its part down to a bar of 280px.
const ROOMY_MIN_WIDTH = (monoWidth('10', POINTS_SIZE) + 2 * SEGMENT_PAD + SEGMENT_GAP_WIDTH) * 10;
const roomy = `@container (min-width: ${ROOMY_MIN_WIDTH}px)` as const;

/**
 * The review rubric as one bar of its 100 points, split into its six parts in their order. The
 * parts share one neutral ink, so no part reads as a palette category, and the gaps between them
 * are the page's own colour. The bar is drawn for the eye; the list under it carries every part's
 * name and points for a screen reader.
 */
export function RubricBar() {
  const captionId = useId();
  return (
    <Box
      component="figure"
      aria-labelledby={captionId}
      sx={{ m: 0, mt: 3.5, mb: 2, fontFamily: typography.mono, containerType: 'inline-size' }}
    >
      <Box id={captionId} sx={{ fontSize: '12px', color: 'var(--ink-muted)', mb: 1 }}>
        {RUBRIC_CAPTION}
      </Box>
      <Box aria-hidden="true" sx={{ display: 'flex', height: 38 }}>
        {RUBRIC_PARTS.map(([name, points], i) => (
          <Box
            key={name}
            sx={{
              flex: `0 0 ${points}%`,
              boxSizing: 'border-box',
              minWidth: 0,
              px: `${SEGMENT_PAD_TIGHT}px`,
              [roomy]: { px: `${SEGMENT_PAD}px` },
              bgcolor: 'var(--ink-muted)',
              color: 'var(--bg-page)',
              fontSize: `${POINTS_SIZE}px`,
              fontWeight: 600,
              lineHeight: '38px',
              borderLeft: i > 0 ? SEGMENT_GAP : 0,
            }}
          >
            {points}
          </Box>
        ))}
      </Box>
      {/* Safari drops a list's role when its markers are off; the role keeps it a list. */}
      <Box
        component="ul"
        role="list"
        sx={{
          listStyle: 'none',
          p: 0,
          m: 0,
          mt: 1.25,
          display: 'grid',
          gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
          gap: '4px 16px',
          [under]: { display: 'flex', gap: 0, mt: 0 },
        }}
      >
        {RUBRIC_PARTS.map(([name, points], i) => (
          <Box
            component="li"
            key={name}
            sx={{
              minWidth: 0,
              fontSize: `${NAME_SIZE}px`,
              lineHeight: 1.35,
              color: 'var(--ink-soft)',
              [under]: {
                flex: `0 0 ${points}%`,
                boxSizing: 'border-box',
                pt: 0.75,
                pr: `${PAD_RIGHT}px`,
                pl: i > 0 ? `${PAD_LEFT}px` : 0,
              },
            }}
          >
            <Box
              component="span"
              sx={{
                display: 'inline-block',
                minWidth: 22,
                color: 'var(--ink)',
                fontWeight: 600,
                [under]: { ...visuallyHiddenSx, minWidth: 0 },
              }}
            >
              {points}
            </Box>{' '}
            {name}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
