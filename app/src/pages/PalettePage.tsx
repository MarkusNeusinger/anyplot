import { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import { PaletteStrip } from '../components/PaletteStrip';
import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { colors, typography, textStyle } from '../theme';

const SWATCHES = [
  { name: 'brand (bluish green)', hex: '#009E73', role: 'first series, primary CTAs, brand anchor' },
  { name: 'vermillion', hex: '#D55E00', role: 'second series, error states, warm contrast' },
  { name: 'blue', hex: '#0072B2', role: 'third series, informational links, cool anchor' },
  { name: 'reddish purple', hex: '#CC79A7', role: 'fourth series, distinctive accent' },
  { name: 'orange', hex: '#E69F00', role: 'fifth series, highlights, hover states' },
  { name: 'sky blue', hex: '#56B4E9', role: 'sixth series, info states' },
  { name: 'yellow', hex: '#F0E442', role: 'seventh series — poor on white, use sparingly' },
  { name: 'neutral (adaptive)', hex: '#1A1A1A / #E8E8E0', role: 'text, gridlines, totals — adapts to theme' },
];

const sectionSx = { py: { xs: 2, md: 3 } };
const proseColumnSx = { maxWidth: 760, mx: 'auto' };

export function PalettePage() {
  const { trackPageview } = useAnalytics();

  useEffect(() => {
    trackPageview('/palette');
  }, [trackPageview]);

  return (
    <>
      <Helmet>
        <title>palette | anyplot.ai</title>
        <meta name="description" content="the Okabe-Ito colorblind-safe palette used across all anyplot.ai visualizations. 8 colors, validated for deuteranopia, protanopia, and tritanopia." />
        <link rel="canonical" href="https://anyplot.ai/palette" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>the Okabe-Ito palette</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              every plot on anyplot.ai uses the Okabe-Ito palette, a set of 8 colors designed to stay
              distinguishable under the main forms of color vision deficiency. Masataka Okabe and Kei Ito
              proposed it on their Color Universal Design page (2002, revised 2008), addressing
              protanopia, deuteranopia, and tritanopia — conditions that affect roughly 8% of men.
            </Box>

            <Box sx={{ ...textStyle, fontStyle: 'italic', borderLeft: `3px solid ${colors.primary}`, pl: 3, my: 4 }}>
              a palette proposed as unambiguous to both colorblind and non-colorblind viewers, with
              vivid colors that stay recognizable on screen and in print.
              <Box component="span" sx={{ display: 'block', mt: 1, fontStyle: 'normal', fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)', letterSpacing: '0.1em' }}>
                — Okabe &amp; Ito, Color Universal Design (2008)
              </Box>
            </Box>
          </Box>

          <Box sx={{ mt: 4 }}>
            <PaletteStrip />
          </Box>
        </Box>

        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>color reference</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {SWATCHES.map((swatch, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1 }}>
                  <Box sx={{
                    width: 40, height: 40, borderRadius: '8px',
                    bgcolor: swatch.hex.includes('/') ? 'var(--ink)' : swatch.hex,
                    flexShrink: 0,
                    border: '1px solid var(--rule)',
                  }} />
                  <Box>
                    <Box sx={{ fontFamily: typography.mono, fontSize: '13px', color: 'var(--ink)', fontWeight: 600 }}>
                      {swatch.hex}
                    </Box>
                    <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>
                      {swatch.name} — {swatch.role}
                    </Box>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>

        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>usage rules</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              the first series in every plot is always the brand color (#009E73). the neutral (position 8)
              is reserved for aggregates and reference lines. yellow (#F0E442) has poor contrast on white
              backgrounds — use it only for position 7 or later.
            </Box>

            <Box sx={textStyle}>
              for sequential data, use viridis or cividis. for diverging data, use BrBG from ColorBrewer.
              don't use Okabe-Ito for continuous data — a categorical palette on continuous data produces
              misleading banding.
            </Box>
          </Box>
        </Box>
      </Box>
    </>
  );
}
