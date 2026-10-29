import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { proseColumnSx, sectionSx } from 'src/sections/palette/paletteHelpers';
import { textStyle, typography } from 'src/theme';

export function ContinuousCmapsSection() {
  return (
    <Box component="section" sx={sectionSx}>
      <SectionHeader prompt="❯" title={<em>continuous cmaps</em>} />
      <Box sx={proseColumnSx}>
        <Box sx={textStyle}>
          for continuous data the categorical pool is replaced with two palette-derived colormaps.
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: 3,
            mt: 2,
          }}
        >
          {/* Sequential */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                mb: 0.5,
              }}
            >
              <Box
                sx={{
                  fontFamily: typography.mono,
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--ink)',
                }}
              >
                imprint_seq
              </Box>
              <Box
                sx={{
                  fontFamily: typography.mono,
                  fontSize: '11px',
                  color: 'var(--ink-muted)',
                }}
              >
                single-polarity · density / magnitude
              </Box>
            </Box>
            <Box
              sx={{
                height: 28,
                borderRadius: 1,
                background: 'linear-gradient(to right, #009E73, #4467A3)',
                boxShadow: '0 0 0 1px var(--rule)',
              }}
            />
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                mt: 0.5,
                fontFamily: typography.mono,
                fontSize: '11px',
                color: 'var(--ink-muted)',
              }}
            >
              <span>#009E73 brand-green</span>
              <span>#4467A3 blue</span>
            </Box>
          </Box>
          {/* Diverging */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                mb: 0.5,
              }}
            >
              <Box
                sx={{
                  fontFamily: typography.mono,
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--ink)',
                }}
              >
                imprint_div
              </Box>
              <Box
                sx={{
                  fontFamily: typography.mono,
                  fontSize: '11px',
                  color: 'var(--ink-muted)',
                }}
              >
                diverging · correlations / signed deviations
              </Box>
            </Box>
            <Box
              sx={{
                height: 28,
                borderRadius: 1,
                background: 'linear-gradient(to right, #AE3030, var(--bg-surface), #4467A3)',
                boxShadow: '0 0 0 1px var(--rule)',
              }}
            />
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                mt: 0.5,
                fontFamily: typography.mono,
                fontSize: '11px',
                color: 'var(--ink-muted)',
              }}
            >
              <span>#AE3030 red</span>
              <span style={{ color: 'var(--ink-muted)' }}>theme-adaptive midpoint</span>
              <span>#4467A3 blue</span>
            </Box>
          </Box>
        </Box>
        <Box
          sx={{
            fontSize: '13px',
            color: 'var(--ink-muted)',
            mt: 2,
            fontFamily: typography.mono,
            lineHeight: 1.55,
          }}
        >
          the diverging midpoint flips per theme — <code>#FAF8F1</code> on cream bg /{' '}
          <code>#1A1A17</code>
          on warm-near-black — so the zero point reads as part of the page rather than as a grey
          blob.
        </Box>
      </Box>
    </Box>
  );
}
