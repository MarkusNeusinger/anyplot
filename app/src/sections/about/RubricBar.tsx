import { useId } from 'react';

import Box from '@mui/material/Box';

import { RUBRIC_CAPTION, RUBRIC_PARTS } from 'src/sections/about/figureData';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import { typography } from 'src/theme';

// Under the bar each name stands beneath its part. The narrowest, a 10-point part, has to hold
// "quality" or "mastery" at 12px with its padding, 72px: 10 % of 720px. Narrower, the names
// leave the bar for a list of two columns under it, each with its points.
const UNDER_MIN_WIDTH = 720;
const under = `@container (min-width: ${UNDER_MIN_WIDTH}px)` as const;

const SEGMENT_GAP = '2px solid var(--bg-page)';

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
              px: 1,
              bgcolor: 'var(--ink-muted)',
              color: 'var(--bg-page)',
              fontSize: '14px',
              fontWeight: 600,
              lineHeight: '38px',
              borderLeft: i > 0 ? SEGMENT_GAP : 0,
            }}
          >
            {points}
          </Box>
        ))}
      </Box>
      <Box
        component="ul"
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
              fontSize: '12px',
              lineHeight: 1.35,
              color: 'var(--ink-soft)',
              [under]: {
                flex: `0 0 ${points}%`,
                boxSizing: 'border-box',
                pt: 0.75,
                pr: 1,
                pl: i > 0 ? 1.25 : 0,
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
