import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';

import { SectionHeader } from 'src/components/SectionHeader';
import type { Swatch } from 'src/pages/PalettePage.helpers';
import {
  proseColumnSx,
  sectionSx,
  textOn,
  tooltipSlotProps,
} from 'src/sections/palette/paletteHelpers';
import { colors, fontSize, typography } from 'src/theme';

const HYBRID_V3_CVD: number[] = [36.19, 16.34, 13.98, 13.98, 13.7, 10.7, 8.81];
const PURE_CVD_GREEDY: number[] = [36.19, 21.45, 19.81, 15.2, 13.7, 10.7, 8.81];

export interface PaletteGridSectionProps {
  sort: 'imprint' | 'cvd';
  setSort: (sort: 'imprint' | 'cvd') => void;
  sortedPalette: Swatch[];
  copiedHex: string | null;
  copyHex: (hex: string) => void;
}

export function PaletteGridSection({
  sort,
  setSort,
  sortedPalette,
  copiedHex,
  copyHex,
}: PaletteGridSectionProps) {
  return (
    <Box component="section" sx={sectionSx}>
      <SectionHeader prompt="❯" title={<em>the 8 categorical hues</em>} />
      <Box sx={proseColumnSx}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            mt: 1,
            mb: 2,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Box
            sx={{
              fontFamily: typography.mono,
              fontSize: fontSize.base,
              fontWeight: 300,
              color: 'var(--ink-muted)',
            }}
          >
            sort:
            {(['imprint', 'cvd'] as const).map(s => (
              <Box
                key={s}
                component="button"
                type="button"
                onClick={() => setSort(s)}
                sx={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  ml: 1,
                  fontFamily: typography.mono,
                  fontSize: fontSize.base,
                  fontWeight: 300,
                  color: sort === s ? colors.primary : 'var(--ink-soft)',
                  textDecoration: 'underline',
                  textDecorationColor: sort === s ? colors.primary : 'var(--rule)',
                  cursor: 'pointer',
                }}
              >
                {s === 'imprint'
                  ? 'imprint (default)'
                  : 'CVD-optimal (max ΔE under colorblindness)'}
              </Box>
            ))}
          </Box>
        </Box>
        {sort === 'cvd' && (
          <Box
            sx={{
              fontFamily: typography.mono,
              lineHeight: 1.55,
              mb: 2,
              p: 2,
              borderLeft: `2px solid ${colors.primary}`,
              backgroundColor: 'var(--bg-surface)',
            }}
          >
            <Box
              sx={{
                fontSize: '11px',
                color: 'var(--ink)',
                fontWeight: 600,
                mb: 1,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              why use CVD-optimal sort?
            </Box>
            <Box sx={{ fontSize: '13px', color: 'var(--ink-soft)', mb: 1.5 }}>
              this ordering picks each next slot by maximising ΔE under the worst of deuteranopia /
              protanopia / tritanopia simulation against the already-placed set. it&apos;s the best
              choice when colour alone has to carry the categorical encoding for users with
              red-green colour vision deficiency — e.g. small-n charts in publications targeting
              CVD-first audiences, status-only legends, or signage-style summary tiles.
            </Box>

            {/* Compact per-n table — only shown in CVD mode since that's where the trade-off matters */}
            <Box sx={{ overflowX: 'auto', mt: 2 }}>
              <Box
                component="table"
                sx={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '11px',
                  '& th, & td': {
                    padding: '4px 10px',
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
                    <th>n series</th>
                    <th style={{ textAlign: 'right' }}>imprint default</th>
                    <th style={{ textAlign: 'right' }}>CVD-optimal (active)</th>
                  </tr>
                </thead>
                <tbody>
                  {HYBRID_V3_CVD.map((de, i) => {
                    const altDe = PURE_CVD_GREEDY[i];
                    const gain = altDe - de;
                    return (
                      <tr key={i}>
                        <td>{i + 2}</td>
                        <td style={{ textAlign: 'right', color: 'var(--ink-muted)' }}>
                          {de.toFixed(2)}
                        </td>
                        <td
                          style={{
                            textAlign: 'right',
                            color: gain > 0 ? '#007A59' : 'var(--ink-muted)',
                            fontWeight: gain > 0 ? 600 : 400,
                          }}
                        >
                          {altDe.toFixed(2)}
                          {gain > 0
                            ? ` (+${gain.toFixed(2)})`
                            : gain < 0
                              ? ` (${gain.toFixed(2)})`
                              : ' (=)'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Box>
            </Box>

            <Box sx={{ fontSize: '13px', color: 'var(--ink-soft)', mt: 2 }}>
              <Box component="strong" sx={{ color: 'var(--ink)' }}>
                trade-off:
              </Box>{' '}
              the first 4 slots end up with two greens (brand at slot 0 + lime at slot 2) and two
              purples (lavender at slot 1 + rose at slot 3) side by side — the eye loses the
              &ldquo;four distinct hue families&rdquo; cue that imprint default gives you. it gains
              +1.22–5.83 ΔE under CVD at n=3..5 (most at n=4); n=2 and n=6..8 are identical, since
              both sortings ship the same 8 hexes.
            </Box>
            <Box sx={{ fontSize: '13px', color: 'var(--ink-muted)', mt: 1 }}>
              <Box component="strong" sx={{ color: 'var(--ink)' }}>
                when to switch:
              </Box>{' '}
              CVD-first audience + small-n (n ≤ 4) + colour is the only encoding. otherwise the
              imprint default is the better balance — and at n = 7..8 you should add a marker shape
              or linestyle either way.
            </Box>
          </Box>
        )}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: 'repeat(2, 1fr)',
              sm: 'repeat(3, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 2,
          }}
        >
          {sortedPalette.map((s, i) => {
            const copied = copiedHex === s.hex;
            return (
              <Box
                key={s.hex}
                component="button"
                type="button"
                aria-label={`Copy ${s.hex} (${s.name}) to clipboard`}
                onClick={() => copyHex(s.hex)}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  textAlign: 'left',
                  '&:hover .v3-sw': { transform: 'scale(1.02)' },
                }}
              >
                <Tooltip
                  placement="top"
                  slotProps={tooltipSlotProps}
                  title={
                    <Box
                      sx={{
                        fontFamily: typography.mono,
                        fontSize: '11px',
                        lineHeight: 1.5,
                        py: 0.5,
                      }}
                    >
                      <Box sx={{ fontWeight: 700, mb: 0.75 }}>
                        {s.name} · {s.hex}
                      </Box>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: 'auto 1fr',
                          columnGap: 1.5,
                          rowGap: 0.75,
                        }}
                      >
                        <Box sx={{ opacity: 0.6 }}>hue · chroma</Box>
                        <Box>
                          {s.H.toFixed(0)}° · {s.C.toFixed(2)}{' '}
                          <Box component="span" sx={{ opacity: 0.6 }}>
                            OKLCH
                          </Box>
                        </Box>

                        <Box sx={{ opacity: 0.6 }}>nearest ΔE</Box>
                        <Box
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: 'auto 1fr',
                            columnGap: 1,
                            rowGap: 0.25,
                          }}
                        >
                          <Box>{s.minNorm.toFixed(1)}</Box>
                          <Box sx={{ opacity: 0.6 }}>normal vision</Box>
                          <Box>{s.minCvd.toFixed(1)}</Box>
                          <Box sx={{ opacity: 0.6 }}>colour-blind</Box>
                        </Box>

                        <Box sx={{ opacity: 0.6 }}>contrast</Box>
                        <Box
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: 'auto 1fr',
                            columnGap: 1,
                            rowGap: 0.25,
                          }}
                        >
                          <Box>{s.wcagL.toFixed(1)}:1</Box>
                          <Box sx={{ opacity: 0.6 }}>on cream</Box>
                          <Box>{s.wcagD.toFixed(1)}:1</Box>
                          <Box sx={{ opacity: 0.6 }}>on dark</Box>
                        </Box>
                      </Box>
                      <Box sx={{ opacity: 0.6, mt: 0.75 }}>higher ΔE = easier to tell apart</Box>
                    </Box>
                  }
                >
                  <Box
                    className="v3-sw"
                    sx={{
                      height: 92,
                      bgcolor: s.hex,
                      color: textOn(s.hex),
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'flex-end',
                      p: 1.25,
                      fontFamily: typography.mono,
                      borderRadius: 1,
                      boxShadow:
                        i === 0 ? `inset 0 0 0 2px var(--ink)` : 'inset 0 0 0 1px var(--rule)',
                      transition: 'transform 0.15s',
                    }}
                  >
                    <Box sx={{ fontSize: '11px', fontWeight: 600, lineHeight: 1.2 }}>{s.name}</Box>
                    <Box sx={{ fontSize: '11px', opacity: 0.85 }}>
                      {copied ? 'copied ✓' : s.hex}
                    </Box>
                  </Box>
                </Tooltip>
                {/* Only the slot + role stay under the swatch; H/C, ΔE and
                      contrast moved into the swatch tooltip (and remain in
                      full in the ΔE matrix + WCAG table below). */}
                <Box
                  sx={{
                    fontFamily: typography.mono,
                    fontSize: '11px',
                    fontWeight: 300,
                    mt: 1,
                    lineHeight: 1.5,
                    color: 'var(--ink-soft)',
                  }}
                >
                  <Box component="span" sx={{ color: 'var(--ink)' }}>
                    slot {i}
                    {i === 0 ? ' ★' : ''}
                  </Box>
                  {' · '}
                  {s.role}
                </Box>
              </Box>
            );
          })}
        </Box>
      </Box>
    </Box>
  );
}
