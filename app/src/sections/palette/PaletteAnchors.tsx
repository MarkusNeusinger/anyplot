import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { textStyle, typography } from 'src/theme';

import { textOn } from './constants';
const sectionSx = { mt: 6 };
const proseColumnSx = { maxWidth: '720px' };
type Anchor = {
  key: string;
  hexLight: string;
  hexDark?: string;
  role: string;
  hint: string;
};

const ANCHORS: Anchor[] = [
  {
    key: 'amber',
    hexLight: '#DDCC77',
    role: 'warning / caution',
    hint: 'Chosen for max ΔE under CVD against lime, so it stays distinct under deuteranopia.',
  },
  {
    key: 'neutral',
    hexLight: '#1A1A17',
    hexDark: '#F0EFE8',
    role: 'totals / baseline / outline',
    hint: "Theme-adaptive ink. Same hex as text and gridlines — the series reads as part of the chart's structural layer.",
  },
  {
    key: 'muted',
    hexLight: '#6B6A63',
    hexDark: '#A8A79F',
    role: 'other / rest / disabled',
    hint: 'Theme-adaptive ink-muted. For "other" / "rest" slices, disabled series, confidence-band fills.',
  },
];

type PaletteAnchorsProps = {
  copiedHex: string | null;
  copyHex: (hex: string) => void;
};

export function PaletteAnchors(props: PaletteAnchorsProps) {
  const { copiedHex, copyHex } = props;
  return (
    <>
      <Box component="section" sx={sectionSx}>
        <SectionHeader prompt="❯" title={<em>semantic anchors</em>} />
        <Box sx={proseColumnSx}>
          <Box sx={textStyle}>
            three additional anchors that live <strong>outside</strong> the categorical pool. they
            are never returned by <code>palette[:n]</code> — reached only by name. two of them flip
            per theme.
          </Box>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
              gap: 2,
              mt: 2,
            }}
          >
            {ANCHORS.map(a => (
              <Box
                key={a.key}
                sx={{
                  border: '1px solid var(--rule)',
                  borderRadius: 2,
                  overflow: 'hidden',
                  backgroundColor: 'var(--bg-surface)',
                }}
              >
                {/* One clickable swatch per hex (amber = 1, adaptive = light + dark);
                      each shows its hex and copies it on click. */}
                <Box sx={{ height: 56, display: 'flex' }}>
                  {(a.hexDark ? [a.hexLight, a.hexDark] : [a.hexLight]).map(hx => {
                    const copied = copiedHex === hx;
                    return (
                      <Box
                        key={hx}
                        component="button"
                        type="button"
                        aria-label={`Copy ${hx} (${a.key}) to clipboard`}
                        onClick={() => copyHex(hx)}
                        sx={{
                          flex: 1,
                          border: 'none',
                          p: 0,
                          pb: 0.75,
                          bgcolor: hx,
                          color: textOn(hx),
                          display: 'flex',
                          alignItems: 'flex-end',
                          justifyContent: 'center',
                          fontFamily: typography.mono,
                          fontSize: '11px',
                          cursor: 'pointer',
                          transition: 'filter 0.15s',
                          '&:hover': { filter: 'brightness(1.06)' },
                        }}
                      >
                        {copied ? 'copied ✓' : hx}
                      </Box>
                    );
                  })}
                </Box>
                <Box sx={{ p: 1.5 }}>
                  <Box
                    sx={{
                      fontFamily: typography.mono,
                      fontSize: '11px',
                      fontWeight: 600,
                      color: 'var(--ink)',
                      mb: 0.5,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    {a.role}
                  </Box>
                  <Box
                    sx={{
                      fontFamily: typography.mono,
                      fontSize: '11px',
                      color: 'var(--ink-muted)',
                      mb: 0.75,
                    }}
                  >
                    palette.{a.key}
                    {a.hexDark ? ' — adaptive' : ''}
                  </Box>
                  <Box sx={{ fontSize: '13px', color: 'var(--ink-muted)', lineHeight: 1.5 }}>
                    {a.hint}
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </>
  );
}
