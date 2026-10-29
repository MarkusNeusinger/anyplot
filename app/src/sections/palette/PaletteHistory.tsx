const proseColumnSx = { maxWidth: '720px' };
import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { typography } from 'src/theme';
import { colors, textStyle } from 'src/theme';

const sectionSx = { mt: 6 };

type HistoryEntry = {
  id: string;
  title: string;
  hexes: string[];
  summary: React.ReactNode;
  href?: string;
  hrefLabel?: string;
};

const HISTORY: HistoryEntry[] = [
  {
    id: 'v3',
    title: 'v3 — imprint (current)',
    hexes: ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD', '#954477', '#99B314'],
    summary:
      "the shipping palette — v1's hues pulled into an even tighter, lower-chroma band so the set reads editorial rather than dashboard and nothing washes out on cream. all six primary hue families are present — red / yellow / green / cyan / blue / purple — which is also why the palette doubles as the site's code-syntax coloring — every token type gets its own colourblind-safe hue. the first four slots span four distinct hue families, and semantic red is deferred to slot 4 so it stays a free named anchor for bad / loss / error instead of landing in every 3-series chart. plus 3 anchors outside the pool: amber, neutral, muted.",
  },
  {
    id: 'v1',
    title: 'v1 — variant D ("balanced")',
    hexes: ['#009E73', '#9418DB', '#B71D27', '#16B8F3', '#99B314', '#D359A7', '#BA843E'],
    summary:
      'anyplot\'s first custom palette — the last one live before v3, and what "anyplot v1 (previous live)" overlays on the wheel above. 7 hues + adaptive neutral. Brand green inherited from Okabe-Ito; the rest from a Petroff-style max-min ΔE search in the muted-paper chroma envelope — separating red from tan and trading the near-yellow for olive-lime so nothing washes out on cream.',
    href: 'https://arxiv.org/abs/2107.02270',
    hrefLabel: 'Petroff 2021 (arXiv)',
  },
  {
    id: 'v0',
    title: 'v0 — Okabe-Ito',
    hexes: ['#009E73', '#D55E00', '#0072B2', '#CC79A7', '#E69F00', '#56B4E9', '#F0E442'],
    summary:
      'The original colorblind-safe categorical palette (Wong 2011, Nature Methods). 7 hues + adaptive neutral, brand green at slot 0 — inherited unchanged by every version since. Its limits on warm paper: orange and vermillion sit only ~30° apart on the hue wheel, and the yellow washes out on cream — both fixed by the later variants.',
    href: 'https://jfly.uni-koeln.de/color/',
    hrefLabel: 'jfly.uni-koeln.de',
  },
];

export function PaletteHistory() {
  return (
    <>
      <Box component="section" sx={sectionSx}>
        <SectionHeader prompt="❯" title={<em>lineage</em>} />
        <Box sx={proseColumnSx}>
          <Box sx={{ ...textStyle, mb: 2.5 }}>
            three versions, each fixing a concrete failure of the last. the interactive hue–chroma
            wheel at the top of the page overlays any of these against imprint.
          </Box>
          <Box
            sx={{
              fontFamily: typography.mono,
              fontSize: '11px',
              color: 'var(--ink-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              mb: 1.5,
            }}
          >
            version timeline
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {HISTORY.map(entry => (
              <Box key={entry.id}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: 2,
                    mb: 1,
                    flexWrap: 'wrap',
                  }}
                >
                  <Box
                    sx={{
                      fontFamily: typography.mono,
                      fontSize: '13px',
                      color: 'var(--ink)',
                      fontWeight: 600,
                    }}
                  >
                    {entry.title}
                  </Box>
                  {entry.href && (
                    <Box
                      component="a"
                      href={entry.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{
                        fontFamily: typography.mono,
                        fontSize: '11px',
                        color: 'var(--ink-soft)',
                        textDecoration: 'underline',
                        textDecorationColor: 'var(--rule)',
                        '&:hover': { color: colors.primary, textDecorationColor: colors.primary },
                      }}
                    >
                      {entry.hrefLabel ?? entry.href}
                    </Box>
                  )}
                </Box>
                <Box
                  sx={{
                    display: 'flex',
                    mb: 1,
                    borderRadius: 1,
                    overflow: 'hidden',
                    boxShadow: '0 0 0 1px var(--rule)',
                  }}
                >
                  {entry.hexes.map(hx => (
                    <Box key={hx} sx={{ flex: 1, height: 32, bgcolor: hx }} title={hx} />
                  ))}
                </Box>
                <Box sx={{ fontSize: '13px', color: 'var(--ink-muted)', lineHeight: 1.55 }}>
                  {entry.summary}
                </Box>
              </Box>
            ))}
          </Box>

          {/* Credit / inspiration + method references */}
          <Box
            sx={{
              mt: 3,
              pt: 2,
              borderTop: '1px solid var(--rule)',
              fontFamily: typography.mono,
              fontSize: '13px',
              color: 'var(--ink-muted)',
              lineHeight: 1.7,
            }}
          >
            colour-harmony and chroma input from Anselm Hahn, whose eye for colour shows in his{' '}
            <Box
              component="a"
              href="https://anselmoo.github.io/dracula-palette/"
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                color: 'var(--ink-soft)',
                textDecoration: 'underline',
                textDecorationColor: 'var(--rule)',
                '&:hover': { color: colors.primary, textDecorationColor: colors.primary },
              }}
            >
              dracula-palette
            </Box>{' '}
            generator. perceptual distances in CAM02-UCS (Petroff 2021); CVD via Machado et al.
            2009.
          </Box>
        </Box>
      </Box>
    </>
  );
}
