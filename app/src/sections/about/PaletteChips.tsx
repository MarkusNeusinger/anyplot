import Box from '@mui/material/Box';

import { useTheme } from 'src/hooks';
import { PALETTE } from 'src/pages/PalettePage.helpers';
import { monoWidth } from 'src/sections/about/monoWidth';
import { typography } from 'src/theme';

const NAME_SIZE = 12;
const GAP = 8;

// Eight chips in a row need eight columns as wide as the longest name, "brand green" at 12px
// (88px where advances are rounded to whole pixels, 84.5px where they are not), and seven 8px
// gaps: 760px, the column's full width. Narrower, they stand four by two, and a long name may
// break.
const ROW_MIN_WIDTH =
  PALETTE.length * Math.max(...PALETTE.map(({ name }) => monoWidth(name, NAME_SIZE))) +
  (PALETTE.length - 1) * GAP;
const row = `@container (min-width: ${ROW_MIN_WIDTH}px)` as const;

export interface PaletteChipsProps {
  /** The id of the element that names the list: the section's heading. */
  labelledBy?: string;
}

/**
 * The palette's eight hues as chips in its order, with the names and hex values the palette page
 * shows. A chip under 3:1 against the page gets the palette page's 1px ink stroke, in the theme
 * that is on, so its edge stays visible; the name and hex under it carry what the colour says.
 */
export function PaletteChips({ labelledBy }: PaletteChipsProps) {
  const { isDark } = useTheme();
  return (
    <Box sx={{ containerType: 'inline-size', mt: 1, mb: 3.5 }}>
      {/* Safari drops a list's role when its markers are off; the role keeps it a list. */}
      <Box
        component="ul"
        role="list"
        aria-labelledby={labelledBy}
        sx={{
          listStyle: 'none',
          p: 0,
          m: 0,
          display: 'grid',
          gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
          gap: `14px ${GAP}px`,
          fontFamily: typography.mono,
          [row]: { gridTemplateColumns: 'repeat(8, minmax(0, 1fr))' },
        }}
      >
        {PALETTE.map(({ hex, name, wcagL, wcagD }) => (
          <Box component="li" key={hex} sx={{ minWidth: 0 }}>
            <Box
              sx={{
                height: 40,
                borderRadius: '3px',
                bgcolor: hex,
                ...((isDark ? wcagD : wcagL) < 3 && {
                  outlineWidth: '1px',
                  outlineStyle: 'solid',
                  outlineColor: 'var(--ink)',
                  outlineOffset: '-1px',
                }),
              }}
            />
            <Box
              sx={{
                mt: 0.75,
                fontSize: `${NAME_SIZE}px`,
                lineHeight: 1.35,
                color: 'var(--ink-soft)',
                [row]: { whiteSpace: 'nowrap' },
              }}
            >
              {name}
            </Box>{' '}
            <Box sx={{ fontSize: '11px', lineHeight: 1.45, color: 'var(--ink-muted)' }}>{hex}</Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
