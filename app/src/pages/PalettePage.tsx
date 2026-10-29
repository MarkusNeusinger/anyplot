import { useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Tooltip from '@mui/material/Tooltip';

import { SectionHeader } from 'src/components/SectionHeader';
import matrixData from 'src/data/paletteMatrices.json';
import { useAnalytics, useTheme } from 'src/hooks';
import { type Lang, PALETTE, snippet, type Swatch } from 'src/pages/PalettePage.helpers';
import { paths } from 'src/routes/paths';
import { ChromaWheel } from 'src/sections/palette/ChromaWheel';
import { CodeBlock } from 'src/sections/palette/CodeBlock';
import { DeltaEMatrix } from 'src/sections/palette/DeltaEMatrix';
import { textOn, tooltipSlotProps } from 'src/sections/palette/paletteHelpers';
import type { Anchor, CompPalette, HistoryEntry, WheelDot } from 'src/sections/palette/types';
import { colors, fontSize, textStyle, typography } from 'src/theme';

// ─────────────────────────────────────────────────────────────────────────────
// Imprint palette — 8 categorical hues + OKLCH coords for the wheel
// ─────────────────────────────────────────────────────────────────────────────

/** Pure-CVD-greedy max-min sort — picks each next slot to maximise ΔE under CVD
 *  against the already-placed set. Best discrimination at n=3..6 but groups
 *  two greens (slot 7 lime + slot 0 brand) and two purples (slot 1 lavender +
 *  slot 3 rose) close together. Order: [brand, lavender, lime, rose, red, cyan, blue, ochre]. */
const CVD_OPTIMAL_ORDER: number[] = [0, 1, 7, 6, 4, 5, 2, 3];

const OKABE_ITO: CompPalette = {
  id: 'okabe',
  name: 'Okabe-Ito',
  href: 'https://jfly.uni-koeln.de/color/',
  hexes: [
    { hex: '#009E73', L: 0.62, C: 0.13, H: 165.5 },
    { hex: '#D55E00', L: 0.621, C: 0.17, H: 47.5 },
    { hex: '#0072B2', L: 0.532, C: 0.131, H: 244.0 },
    { hex: '#CC79A7', L: 0.679, C: 0.118, H: 346.3 },
    { hex: '#E69F00', L: 0.753, C: 0.158, H: 76.8 },
    { hex: '#56B4E9', L: 0.735, C: 0.117, H: 236.2 },
    { hex: '#F0E442', L: 0.902, C: 0.172, H: 105.0 },
  ],
};

const TOL_MUTED: CompPalette = {
  id: 'tol',
  name: 'Tol muted',
  href: 'https://personal.sron.nl/~pault/',
  hexes: [
    { hex: '#332288', L: 0.347, C: 0.159, H: 281.8 },
    { hex: '#88CCEE', L: 0.812, C: 0.084, H: 230.8 },
    { hex: '#44AA99', L: 0.674, C: 0.098, H: 180.4 },
    { hex: '#117733', L: 0.499, C: 0.135, H: 148.6 },
    { hex: '#999933', L: 0.663, C: 0.123, H: 109.3 },
    { hex: '#DDCC77', L: 0.841, C: 0.108, H: 98.3 },
    { hex: '#CC6677', L: 0.635, C: 0.13, H: 11.0 },
    { hex: '#882255', L: 0.432, C: 0.145, H: 354.5 },
    { hex: '#AA4499', L: 0.553, C: 0.167, H: 334.6 },
  ],
};

const SET2: CompPalette = {
  id: 'set2',
  name: 'ColorBrewer Set2',
  href: 'https://colorbrewer2.org',
  hexes: [
    { hex: '#66C2A5', L: 0.749, C: 0.099, H: 170.8 },
    { hex: '#FC8D62', L: 0.755, C: 0.147, H: 41.5 },
    { hex: '#8DA0CB', L: 0.707, C: 0.067, H: 266.1 },
    { hex: '#E78AC3', L: 0.748, C: 0.132, H: 343.3 },
    { hex: '#A6D854', L: 0.821, C: 0.169, H: 127.3 },
    { hex: '#FFD92F', L: 0.892, C: 0.173, H: 95.2 },
    { hex: '#E5C494', L: 0.837, C: 0.073, H: 76.8 },
    { hex: '#B3B3B3', L: 0.767, C: 0.0, H: 89.9 },
  ],
};

const ANYPLOT_PREV: CompPalette = {
  id: 'prev',
  name: 'anyplot v1 (previous live)',
  hexes: [
    { hex: '#009E73', L: 0.62, C: 0.13, H: 165.5 },
    { hex: '#9418DB', L: 0.529, C: 0.259, H: 307.4 },
    { hex: '#B71D27', L: 0.503, C: 0.187, H: 24.7 },
    { hex: '#16B8F3', L: 0.735, C: 0.145, H: 231.0 },
    { hex: '#99B314', L: 0.722, C: 0.167, H: 119.8 },
    { hex: '#D359A7', L: 0.643, C: 0.176, H: 344.0 },
    { hex: '#BA843E', L: 0.654, C: 0.109, H: 70.8 },
  ],
};

const COMPARISONS: CompPalette[] = [OKABE_ITO, TOL_MUTED, SET2, ANYPLOT_PREV];

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

const HYBRID_V3_CVD: number[] = [36.19, 16.34, 13.98, 13.98, 13.7, 10.7, 8.81];
const PURE_CVD_GREEDY: number[] = [36.19, 21.45, 19.81, 15.2, 13.7, 10.7, 8.81];

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

// ─────────────────────────────────────────────────────────────────────────────
// Code snippets per language
// ─────────────────────────────────────────────────────────────────────────────

const LANG_LABELS: Record<Lang, string> = {
  python: 'Python',
  r: 'R',
  julia: 'Julia',
  js: 'JavaScript',
};

// ─────────────────────────────────────────────────────────────────────────────
// ΔE distance matrix — generated by scripts/palette-matrix-export.py
// ─────────────────────────────────────────────────────────────────────────────

const DE_LEGEND: { label: string; bg: string }[] = [
  { label: '<5 indistinct', bg: 'rgba(174, 48, 48, 0.26)' },
  { label: '<10 weak', bg: 'rgba(189, 130, 51, 0.22)' },
  { label: '<15 acceptable', bg: 'rgba(221, 204, 119, 0.18)' },
  { label: '≥15 comfortable', bg: 'transparent' },
];

// ─────────────────────────────────────────────────────────────────────────────
// Layout
// ─────────────────────────────────────────────────────────────────────────────

const sectionSx = { py: { xs: 2, md: 3 } };
const proseColumnSx = { maxWidth: 880, mx: 'auto' };

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export function PalettePage() {
  const { trackPageview } = useAnalytics();
  const { isDark } = useTheme();
  const [lang, setLang] = useState<Lang>('python');
  const [oklch, setOklch] = useState(false);
  const [compareId, setCompareId] = useState<string | null>(null);
  /** `imprint` = hybrid-v3 (default, 4 hue families up front).
   *  `cvd` = pure-CVD-greedy max-min (best per-n ΔE under CVD, but groups
   *  two greens + two purples close together in the first 4 slots). */
  const [sort, setSort] = useState<'imprint' | 'cvd'>('imprint');
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  /** Hero wheel: collapsed = small preview; expanded = larger + comparison toggles. */
  const [wheelOpen, setWheelOpen] = useState(false);

  const copyHex = (hex: string) => {
    void navigator.clipboard
      .writeText(hex)
      .then(() => {
        setCopiedHex(hex);
        setTimeout(() => setCopiedHex(c => (c === hex ? null : c)), 1500);
      })
      .catch(() => {
        // Silently ignore — clipboard API can fail in insecure contexts.
      });
  };

  useEffect(() => {
    trackPageview(paths.palette);
  }, [trackPageview]);

  const sortedPalette: Swatch[] = useMemo(
    () => (sort === 'imprint' ? PALETTE : CVD_OPTIMAL_ORDER.map(i => PALETTE[i])),
    [sort]
  );

  // Wheel dots are positioned by hue + chroma, independent of sort order —
  // we keep the canonical PALETTE order so the brand-green outline stays on
  // the same identity dot regardless of sort.
  const imprintDots: WheelDot[] = useMemo(
    () => PALETTE.map(s => ({ hex: s.hex, L: s.L, C: s.C, H: s.H, name: s.name })),
    []
  );
  const overlayDots: WheelDot[] | undefined = useMemo(
    () => COMPARISONS.find(c => c.id === compareId)?.hexes,
    [compareId]
  );

  return (
    <>
      <>
        <title>imprint palette | anyplot.ai</title>
        <meta
          name="description"
          content="imprint — anyplot's categorical palette: 8 colorblind-safe hues plus 3 semantic anchors (amber, neutral, muted), tuned for warm-paper rendering and validated against deuteranopia / protanopia / tritanopia."
        />
        <meta property="og:title" content="imprint palette | anyplot.ai" />
        <meta
          property="og:description"
          content="imprint — anyplot's colorblind-safe categorical palette: 8 hues plus 3 semantic anchors."
        />
        <link rel="canonical" href="https://anyplot.ai/palette" />
      </>

      <Box sx={{ pb: 4 }}>
        {/* 1. HERO — short lede + a compact hue–chroma wheel. Click the wheel to
            enlarge it and reveal the palette-comparison toggles. */}
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
                  semantic anchors. low-chroma and warm-tinted for cream paper, the same hues on
                  dark, validated against deuteranopia / protanopia / tritanopia. built to let the
                  data speak.
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
                      hue counter-clockwise from 3 o&apos;clock · chroma = distance from centre · ★
                      = brand · shaded band = imprint&apos;s low-chroma corridor
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

        {/* 2. PALETTE GRID + SORT TOGGLE */}
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
                  this ordering picks each next slot by maximising ΔE under the worst of
                  deuteranopia / protanopia / tritanopia simulation against the already-placed set.
                  it&apos;s the best choice when colour alone has to carry the categorical encoding
                  for users with red-green colour vision deficiency — e.g. small-n charts in
                  publications targeting CVD-first audiences, status-only legends, or signage-style
                  summary tiles.
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
                  the first 4 slots end up with two greens (brand at slot 0 + lime at slot 2) and
                  two purples (lavender at slot 1 + rose at slot 3) side by side — the eye loses the
                  &ldquo;four distinct hue families&rdquo; cue that imprint default gives you. it
                  gains +1.22–5.83 ΔE under CVD at n=3..5 (most at n=4); n=2 and n=6..8 are
                  identical, since both sortings ship the same 8 hexes.
                </Box>
                <Box sx={{ fontSize: '13px', color: 'var(--ink-muted)', mt: 1 }}>
                  <Box component="strong" sx={{ color: 'var(--ink)' }}>
                    when to switch:
                  </Box>{' '}
                  CVD-first audience + small-n (n ≤ 4) + colour is the only encoding. otherwise the
                  imprint default is the better balance — and at n = 7..8 you should add a marker
                  shape or linestyle either way.
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
                          <Box sx={{ opacity: 0.6, mt: 0.75 }}>
                            higher ΔE = easier to tell apart
                          </Box>
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
                        <Box sx={{ fontSize: '11px', fontWeight: 600, lineHeight: 1.2 }}>
                          {s.name}
                        </Box>
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

        {/* 3. SEMANTIC ANCHORS */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>semantic anchors</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              three additional anchors that live <strong>outside</strong> the categorical pool. they
              are never returned by <code>palette[:n]</code> — reached only by name. two of them
              flip per theme.
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

        {/* 3b. CONTINUOUS CMAPS — sequential + diverging */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>continuous cmaps</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              for continuous data the categorical pool is replaced with two palette-derived
              colormaps.
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

        {/* 4. COPY SNIPPETS */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>copy &amp; paste</em>} />
          <Box sx={proseColumnSx}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 2,
                mt: 2,
              }}
            >
              <Tabs
                value={lang}
                onChange={(_, v) => setLang(v as Lang)}
                variant="scrollable"
                scrollButtons="auto"
                sx={{
                  minHeight: 36,
                  '& .MuiTab-root': {
                    fontFamily: typography.mono,
                    fontSize: '11px',
                    minHeight: 36,
                    py: 0,
                    textTransform: 'none',
                    color: 'var(--ink-muted)',
                  },
                  '& .Mui-selected': { color: 'var(--ink)' },
                  '& .MuiTabs-indicator': { backgroundColor: colors.primary },
                }}
              >
                {(Object.keys(LANG_LABELS) as Lang[]).map(l => (
                  <Tab key={l} value={l} label={LANG_LABELS[l]} />
                ))}
              </Tabs>
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={oklch}
                    onChange={e => setOklch(e.target.checked)}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: colors.primary },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                        backgroundColor: colors.primary,
                      },
                    }}
                  />
                }
                label={
                  <Box
                    sx={{
                      fontFamily: typography.mono,
                      fontSize: '11px',
                      color: 'var(--ink-muted)',
                    }}
                  >
                    OKLCH
                  </Box>
                }
              />
            </Box>
            <CodeBlock code={snippet(lang, oklch, sortedPalette)} />
          </Box>
        </Box>

        {/* 5. CONTRAST (WCAG) */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>WCAG contrast</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              muted palettes share a known limit: the lighter members carry their distinguishability
              through chroma, not L-spread. On cream bg <code>#F5F3EC</code>, four categorical hues
              + amber fall under WCAG 2.1 SC 1.4.11&apos;s 3:1 minimum. The industry-standard fix is
              a <strong>1px ink-color stroke</strong> on affected series — but it&apos;s a renderer
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

        {/* 6. ΔE COLOUR DISTANCE — pairwise distances generated by
            scripts/palette-matrix-export.py (CAM02-UCS + Machado-2009 CVD). */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>ΔE colour distance</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              the numbers behind each hue&apos;s <code>norm</code> / <code>cvd</code> readout, in
              full — pairwise ΔE in CAM02-UCS for the 8 hues plus the amber and neutral anchors.
              lower = closer = harder to tell apart. the worst-CVD grid takes the lowest of the
              deuteranopia / protanopia / tritanopia simulations per pair; hover any cell for the
              breakdown.
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
                thresholds: Petroff 2021 · amber + neutral (light-theme ink) sit outside the
                categorical pool
              </Box>
            </Box>
          </Box>
        </Box>

        {/* 7. HISTORY */}
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
      </Box>
    </>
  );
}
