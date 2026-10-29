import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import matrixData from 'src/data/paletteMatrices.json';
import { DeltaEMatrix } from 'src/sections/palette/DeltaEMatrix';
import { proseColumnSx, sectionSx } from 'src/sections/palette/paletteHelpers';
import { textStyle, typography } from 'src/theme';

const DE_LEGEND: { label: string; bg: string }[] = [
  { label: '<5 indistinct', bg: 'rgba(174, 48, 48, 0.26)' },
  { label: '<10 weak', bg: 'rgba(189, 130, 51, 0.22)' },
  { label: '<15 acceptable', bg: 'rgba(221, 204, 119, 0.18)' },
  { label: '≥15 comfortable', bg: 'transparent' },
];

export function DeltaESection() {
  return (
    <Box component="section" sx={sectionSx}>
      <SectionHeader prompt="❯" title={<em>ΔE colour distance</em>} />
      <Box sx={proseColumnSx}>
        <Box sx={textStyle}>
          the numbers behind each hue&apos;s <code>norm</code> / <code>cvd</code> readout, in full —
          pairwise ΔE in CAM02-UCS for the 8 hues plus the amber and neutral anchors. lower = closer
          = harder to tell apart. the worst-CVD grid takes the lowest of the deuteranopia /
          protanopia / tritanopia simulations per pair; hover any cell for the breakdown.
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: 6,
            mt: 2,
          }}
        >
          <DeltaEMatrix title="normal vision" matrix={matrixData.matrices.normal} />
          <DeltaEMatrix
            title="worst of deuter / protan / tritan"
            matrix={matrixData.matrices.worstCvd}
            breakdown={[
              { label: 'deut', m: matrixData.matrices.deuter },
              { label: 'prot', m: matrixData.matrices.protan },
              { label: 'trit', m: matrixData.matrices.tritan },
            ]}
          />
        </Box>
        <Box
          sx={{
            mt: 2,
            fontFamily: typography.mono,
            fontSize: '11px',
            color: 'var(--ink-muted)',
          }}
        >
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            {DE_LEGEND.map(l => (
              <Box key={l.label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box
                  sx={{ width: 13, height: 13, bgcolor: l.bg, border: '1px solid var(--rule)' }}
                />
                {l.label}
              </Box>
            ))}
          </Box>
          <Box sx={{ mt: 0.75 }}>
            thresholds: Petroff 2021 · amber + neutral (light-theme ink) sit outside the categorical
            pool
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
