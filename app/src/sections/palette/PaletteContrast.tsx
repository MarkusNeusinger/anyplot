import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { useTheme } from 'src/hooks';
import { textStyle, typography } from 'src/theme';

const sectionSx = { mt: 6 };
const proseColumnSx = { maxWidth: '720px' };
const WCAG_TABLE: { hex: string; name: string; light: number; dark: number }[] = [
  { hex: '#009E73', name: 'brand-green', light: 3.08, dark: 5.48 },
  { hex: '#AE3030', name: 'matte-red', light: 5.79, dark: 2.92 },
  { hex: '#C475FD', name: 'lavender', light: 2.59, dark: 6.53 },
  { hex: '#99B314', name: 'lime', light: 2.15, dark: 7.87 },
  { hex: '#4467A3', name: 'blue', light: 5.09, dark: 3.32 },
  { hex: '#2ABCCD', name: 'cyan', light: 2.06, dark: 8.19 },
  { hex: '#954477', name: 'rose', light: 5.61, dark: 3.01 },
  { hex: '#BD8233', name: 'ochre', light: 2.95, dark: 5.72 },
  { hex: '#DDCC77', name: 'amber', light: 1.46, dark: 11.59 },
];

export function PaletteContrast() {
  const { isDark } = useTheme();

  return (
    <>
      <Box component="section" sx={sectionSx}>
        <SectionHeader prompt="❯" title={<em>WCAG contrast</em>} />
        <Box sx={proseColumnSx}>
          <Box sx={textStyle}>
            muted palettes share a known limit: the lighter members carry their distinguishability
            through chroma, not L-spread. On cream bg <code>#F5F3EC</code>, four categorical hues +
            amber fall under WCAG 2.1 SC 1.4.11&apos;s 3:1 minimum. The industry-standard fix is a{' '}
            <strong>1px ink-color stroke</strong> on affected series — but it&apos;s a renderer
            judgment call, not a hard rule. the swatches below carry that stroke wherever a series
            fails in the current theme.
          </Box>
          <Box sx={{ mt: 2, overflowX: 'auto' }}>
            <Box
              component="table"
              sx={{
                width: '100%',
                borderCollapse: 'collapse',
                fontFamily: typography.mono,
                fontSize: '11px',
                '& th, & td': {
                  padding: '6px 12px',
                  textAlign: 'left',
                  borderBottom: '1px solid var(--rule)',
                },
                '& th': {
                  color: 'var(--ink-muted)',
                  fontWeight: 600,
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                },
              }}
            >
              <thead>
                <tr>
                  <th>hex</th>
                  <th>name</th>
                  <th style={{ textAlign: 'right' }}>on cream</th>
                  <th style={{ textAlign: 'right' }}>on dark</th>
                </tr>
              </thead>
              <tbody>
                {WCAG_TABLE.map(row => {
                  // Live demo of the intro's fix: in the current theme the failing (✗) series get
                  // the 1px ink-color stroke on their swatch. The affected set flips per theme (light
                  // hues fail on cream, dark hues fail on dark) and --ink adapts, so each swatch shows
                  // the fix exactly as it would render.
                  const affected = isDark ? row.dark < 3 : row.light < 3;
                  return (
                    <tr key={row.hex}>
                      <td>
                        <Box
                          component="span"
                          sx={{
                            display: 'inline-block',
                            width: 16,
                            height: 16,
                            borderRadius: 2,
                            bgcolor: row.hex,
                            mr: 1,
                            verticalAlign: 'middle',
                            border: affected ? '1px solid var(--ink)' : '1px solid var(--rule)',
                          }}
                        />
                        {row.hex}
                      </td>
                      <td style={{ color: 'var(--ink-muted)' }}>{row.name}</td>
                      <td
                        style={{
                          textAlign: 'right',
                          color: row.light < 3 ? '#b62d2d' : '#007A59',
                          fontWeight: 600,
                        }}
                      >
                        {row.light.toFixed(2)}:1 {row.light < 3 ? '✗' : '✓'}
                      </td>
                      <td
                        style={{
                          textAlign: 'right',
                          color: row.dark < 3 ? '#b62d2d' : '#007A59',
                          fontWeight: 600,
                        }}
                      >
                        {row.dark.toFixed(2)}:1 {row.dark < 3 ? '✗' : '✓'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Box>
          </Box>
        </Box>
      </Box>
    </>
  );
}
