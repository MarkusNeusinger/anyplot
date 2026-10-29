import type { Dispatch, SetStateAction } from 'react';

import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';

import { SectionHeader } from 'src/components/SectionHeader';
import { ChromaWheel } from 'src/sections/palette/ChromaWheel';
import { COMPARISONS, proseColumnSx, sectionSx } from 'src/sections/palette/paletteHelpers';
import type { WheelDot } from 'src/sections/palette/types';
import { colors, textStyle, typography } from 'src/theme';

export interface HeroSectionProps {
  wheelOpen: boolean;
  setWheelOpen: Dispatch<SetStateAction<boolean>>;
  imprintDots: WheelDot[];
  overlayDots: WheelDot[] | undefined;
  compareId: string | null;
  setCompareId: Dispatch<SetStateAction<string | null>>;
}

export function HeroSection({
  wheelOpen,
  setWheelOpen,
  imprintDots,
  overlayDots,
  compareId,
  setCompareId,
}: HeroSectionProps) {
  return (
    <Box component="section" sx={sectionSx}>
      <SectionHeader prompt="❯" title={<em>anyplot&apos;s imprint palette</em>} />
      <Box sx={{ ...proseColumnSx, mt: 3 }}>
        {/* sm+: wheel on the left, content (lede + comparison) on the right.
            When expanded the comparison panel fills the column beside the
            wheel rather than floating below it, so the tall wheel is balanced. */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 2.5, sm: 4 },
            alignItems: { xs: 'center', sm: wheelOpen ? 'flex-start' : 'center' },
          }}
        >
          {/* Wheel column — the button toggles the expanded comparison view */}
          <Box
            sx={{
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 0.75,
            }}
          >
            <Box
              component="button"
              type="button"
              onClick={() => setWheelOpen(o => !o)}
              aria-expanded={wheelOpen}
              aria-label={
                wheelOpen
                  ? 'Collapse the hue–chroma wheel'
                  : 'Expand the hue–chroma wheel to compare palettes'
              }
              sx={{
                background: 'none',
                border: 'none',
                p: 0,
                m: 0,
                cursor: 'pointer',
                lineHeight: 0,
                borderRadius: '50%',
                transition: 'transform 0.15s',
                '&:hover': { transform: 'scale(1.03)' },
                '&:focus-visible': {
                  outline: `2px solid ${colors.primary}`,
                  outlineOffset: '3px',
                },
              }}
            >
              <ChromaWheel
                size={wheelOpen ? 300 : 128}
                compact={!wheelOpen}
                imprintDots={imprintDots}
                overlay={wheelOpen ? overlayDots : undefined}
              />
            </Box>
            <Box
              sx={{
                fontFamily: typography.mono,
                fontSize: '11px',
                color: wheelOpen ? 'var(--ink-muted)' : colors.primary,
              }}
            >
              {wheelOpen ? 'click to close' : 'compare ▸'}
            </Box>
          </Box>

          {/* Content column — lede, then the comparison panel when expanded */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={textStyle}>
              <strong>imprint</strong> is anyplot&apos;s categorical palette — 8 hues plus 3
              semantic anchors. low-chroma and warm-tinted for cream paper, the same hues on dark,
              validated against deuteranopia / protanopia / tritanopia. built to let the data speak.
            </Box>

            <Collapse in={wheelOpen}>
              <Box sx={{ mt: 2.5, borderTop: '1px solid var(--rule)', pt: 2.5 }}>
                <Box sx={{ fontSize: '13px', color: 'var(--ink-soft)', lineHeight: 1.6 }}>
                  where imprint sits in hue–chroma space — eight hues inside a narrow low-chroma
                  band, spread evenly around the wheel. overlay another published categorical
                  palette to compare:
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1.5 }}>
                  {COMPARISONS.map(c => {
                    const active = compareId === c.id;
                    return (
                      <Box
                        key={c.id}
                        component="button"
                        type="button"
                        aria-pressed={active}
                        onClick={() => setCompareId(active ? null : c.id)}
                        sx={{
                          background: active ? 'var(--bg-surface)' : 'none',
                          border: `1px solid ${active ? colors.primary : 'var(--rule)'}`,
                          borderRadius: 1,
                          padding: '6px 10px',
                          fontFamily: typography.mono,
                          fontSize: '11px',
                          color: active ? colors.primary : 'var(--ink-soft)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          '&:hover': { borderColor: colors.primary, color: colors.primary },
                        }}
                      >
                        <Box
                          sx={{
                            display: 'flex',
                            borderRadius: 0.5,
                            overflow: 'hidden',
                            boxShadow: '0 0 0 1px var(--rule)',
                          }}
                        >
                          {c.hexes.map(d => (
                            <Box key={d.hex} sx={{ width: 8, height: 14, bgcolor: d.hex }} />
                          ))}
                        </Box>
                        {c.name}
                      </Box>
                    );
                  })}
                </Box>
                <Box
                  sx={{
                    fontFamily: typography.mono,
                    fontSize: '11px',
                    color: 'var(--ink-muted)',
                    mt: 1.75,
                    lineHeight: 1.5,
                  }}
                >
                  hue counter-clockwise from 3 o&apos;clock · chroma = distance from centre · ★ =
                  brand · shaded band = imprint&apos;s low-chroma corridor
                  {compareId && (
                    <Box component="span">
                      {' '}
                      · rings = {COMPARISONS.find(c => c.id === compareId)?.name}
                    </Box>
                  )}
                </Box>
              </Box>
            </Collapse>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
