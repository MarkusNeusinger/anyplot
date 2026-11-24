import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import {
  divStops,
  proseColumnSx,
  rampGradient,
  type RampStops,
  type RampTheme,
  type RampUse,
  sectionSx,
  SEQ_STOPS,
} from 'src/sections/palette/paletteHelpers';
import { textStyle, typography } from 'src/theme';

const USE_LABEL: Record<RampUse, string> = {
  fields: 'fields · heatmaps / maps / filled contours',
  marks: 'marks · points / lines / bars on the page',
};

const monoSx = { fontFamily: typography.mono, fontSize: '11px' };

function RampRow({ name, use, stops }: { name: string; use: RampUse; stops: RampStops }) {
  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          gap: 1,
          mb: 0.5,
        }}
      >
        <Box sx={{ ...monoSx, fontWeight: 600, color: 'var(--ink)' }}>{name}</Box>
        <Box sx={{ ...monoSx, color: 'var(--ink-muted)', textAlign: 'right' }}>
          {USE_LABEL[use]}
        </Box>
      </Box>
      <Box
        data-testid={`${name}-${use}`}
        sx={{
          height: 28,
          borderRadius: 1,
          background: rampGradient(stops),
          boxShadow: '0 0 0 1px var(--rule)',
        }}
      />
      <Box
        sx={{
          ...monoSx,
          display: 'flex',
          justifyContent: 'space-between',
          mt: 0.5,
          color: 'var(--ink-muted)',
        }}
      >
        {stops.hex.map(colour => (
          <span key={colour}>{colour}</span>
        ))}
      </Box>
    </Box>
  );
}

export interface ContinuousCmapsSectionProps {
  isDark: boolean;
}

export function ContinuousCmapsSection({ isDark }: ContinuousCmapsSectionProps) {
  const theme: RampTheme = isDark ? 'dark' : 'light';
  return (
    <Box component="section" sx={sectionSx}>
      <SectionHeader prompt="❯" title={<em>continuous cmaps</em>} />
      <Box sx={proseColumnSx}>
        <Box sx={textStyle}>
          for continuous data the categorical pool is replaced with two palette-derived ramps. each
          has its own stops per theme and per use: <strong>fields</strong> for cells that fill the
          plot, <strong>marks</strong> for points, lines and bars that sit on the page. shown here
          in the {theme} theme; switch it and the stops change.
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: 3,
            mt: 2,
          }}
        >
          <Box sx={{ display: 'grid', gap: 2 }}>
            <RampRow name="imprint_seq" use="fields" stops={SEQ_STOPS.fields[theme]} />
            <RampRow name="imprint_seq" use="marks" stops={SEQ_STOPS.marks[theme]} />
          </Box>
          <Box sx={{ display: 'grid', gap: 2 }}>
            <RampRow name="imprint_div" use="fields" stops={divStops('fields', theme)} />
            <RampRow name="imprint_div" use="marks" stops={divStops('marks', theme)} />
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
          in both themes high values stand out from the page and low values recede into it: the
          sequential ramp runs light → dark on cream and dark → bright on warm-near-black. fields
          span the wider lightness range; every colour of the sequential marks ramp keeps 3:1
          against its page. the diverging midpoint is the page for fields; for marks it is a grey
          that keeps at least 3:1 against the page, level with the poles, so a point at zero stays
          visible and the extremes lead.
        </Box>
      </Box>
    </Box>
  );
}
