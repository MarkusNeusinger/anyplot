import Box from '@mui/material/Box';

import { useTheme } from 'src/hooks';
import { PALETTE } from 'src/pages/PalettePage.helpers';
import { typography } from 'src/theme';

// Eight chips in a row need eight columns as wide as "brand green" at 12px (84.5px in MonoLisa)
// and seven 8px gaps: 732px. Narrower, they stand four by two, and a long name may break.
const ROW_MIN_WIDTH = 732;
const row = `@container (min-width: ${ROW_MIN_WIDTH}px)` as const;

/**
 * The palette's eight hues as chips in its order, with the names and hex values the palette page
 * shows. A chip under 3:1 against the page gets the palette page's 1px ink stroke, in the theme
 * that is on, so its edge stays visible; the name and hex under it carry what the colour says.
 */
export function PaletteChips() {
  const { isDark } = useTheme();
  return (
    <Box sx={{ containerType: 'inline-size', mt: 1, mb: 3.5 }}>
      {/* Safari drops a list's role when its markers are off; the role keeps it a list. */}
      <Box
        component="ul"
        role="list"
        sx={{
          listStyle: 'none',
          p: 0,
          m: 0,
          display: 'grid',
          gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
          gap: '14px 8px',
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
                fontSize: '12px',
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
