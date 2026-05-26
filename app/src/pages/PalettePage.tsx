import { useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Tooltip from '@mui/material/Tooltip';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { PaletteStrip } from '../components/PaletteStrip';
import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { colors, typography, textStyle } from '../theme';

// ─────────────────────────────────────────────────────────────────────────────
// Imprint palette — 8 categorical hues + OKLCH coords for the wheel
// ─────────────────────────────────────────────────────────────────────────────

type Swatch = {
  hex: string;
  name: string;
  family: string;
  role: string;
  L: number;
  C: number;
  H: number;
  oklch: string;
  /** Per-hex min ΔE to any other imprint member under normal vision. */
  minNorm: number;
  /** Per-hex min ΔE to any other imprint member under worst CVD sim (deuter / protan / tritan). */
  minCvd: number;
  /** WCAG contrast on cream bg #F5F3EC. */
  wcagL: number;
  /** WCAG contrast on warm near-black bg #121210. */
  wcagD: number;
};

const PALETTE: Swatch[] = [
  { hex: '#009E73', name: 'brand green', family: 'green',  role: 'first series',       L: 0.620, C: 0.130, H: 165.5, oklch: 'oklch(0.620 0.130 165.5)', minNorm: 22.51, minCvd: 13.70, wcagL: 3.08, wcagD: 5.48 },
  { hex: '#C475FD', name: 'lavender',    family: 'purple', role: 'creative',           L: 0.704, C: 0.202, H: 308.9, oklch: 'oklch(0.704 0.202 308.9)', minNorm: 30.03, minCvd: 13.81, wcagL: 2.59, wcagD: 6.53 },
  { hex: '#4467A3', name: 'blue',        family: 'blue',   role: 'cool / info',        L: 0.516, C: 0.104, H: 260.6, oklch: 'oklch(0.516 0.104 260.6)', minNorm: 32.35, minCvd: 10.70, wcagL: 5.09, wcagD: 3.32 },
  { hex: '#BD8233', name: 'ochre',       family: 'yellow', role: 'earth / commodity',  L: 0.652, C: 0.118, H: 70.5,  oklch: 'oklch(0.652 0.118 70.5)',  minNorm: 24.00, minCvd: 8.81,  wcagL: 2.95, wcagD: 5.72 },
  { hex: '#AE3030', name: 'matte red',   family: 'red',    role: 'bad / loss / error', L: 0.503, C: 0.163, H: 25.2,  oklch: 'oklch(0.503 0.163 25.2)',  minNorm: 20.73, minCvd: 15.20, wcagL: 5.79, wcagD: 2.92 },
  { hex: '#2ABCCD', name: 'cyan',        family: 'cyan',   role: 'sky / tech-cool',    L: 0.730, C: 0.117, H: 207.1, oklch: 'oklch(0.730 0.117 207.1)', minNorm: 22.51, minCvd: 13.70, wcagL: 2.06, wcagD: 8.19 },
  { hex: '#954477', name: 'rose',        family: 'purple', role: 'wellness / health',  L: 0.508, C: 0.125, H: 343.9, oklch: 'oklch(0.508 0.125 343.9)', minNorm: 20.73, minCvd: 10.70, wcagL: 5.61, wcagD: 3.01 },
  { hex: '#99B314', name: 'lime',        family: 'green',  role: 'growth / nature',    L: 0.722, C: 0.167, H: 119.8, oklch: 'oklch(0.722 0.167 119.8)', minNorm: 24.00, minCvd: 8.81,  wcagL: 2.15, wcagD: 7.87 },
];

/** Pure-CVD-greedy max-min sort — picks each next slot to maximise ΔE under CVD
 *  against the already-placed set. Best discrimination at n=3..6 but groups
 *  two greens (slot 7 lime + slot 0 brand) and two purples (slot 1 lavender +
 *  slot 3 rose) close together. Order: [brand, lavender, lime, rose, red, cyan, blue, ochre]. */
const CVD_OPTIMAL_ORDER: number[] = [0, 1, 7, 6, 4, 5, 2, 3];

type CompPalette = { id: string; name: string; href?: string; hexes: { hex: string; L: number; C: number; H: number }[] };

const OKABE_ITO: CompPalette = {
  id: 'okabe',
  name: 'Okabe-Ito',
  href: 'https://jfly.uni-koeln.de/color/',
  hexes: [
    { hex: '#009E73', L: 0.620, C: 0.130, H: 165.5 },
    { hex: '#D55E00', L: 0.621, C: 0.170, H: 47.5 },
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
    { hex: '#CC6677', L: 0.635, C: 0.130, H: 11.0 },
    { hex: '#882255', L: 0.432, C: 0.145, H: 354.5 },
    { hex: '#AA4499', L: 0.553, C: 0.167, H: 334.6 },
  ],
};

const VARIANT_D: CompPalette = {
  id: 'd',
  name: 'anyplot variant D (previous)',
  hexes: [
    { hex: '#009E73', L: 0.620, C: 0.130, H: 165.5 },
    { hex: '#9418DB', L: 0.529, C: 0.259, H: 307.4 },
    { hex: '#B71D27', L: 0.503, C: 0.187, H: 24.7 },
    { hex: '#16B8F3', L: 0.735, C: 0.145, H: 231.0 },
    { hex: '#99B314', L: 0.722, C: 0.167, H: 119.8 },
    { hex: '#D359A7', L: 0.643, C: 0.176, H: 344.0 },
    { hex: '#BA843E', L: 0.654, C: 0.109, H: 70.8 },
  ],
};

const COMPARISONS: CompPalette[] = [OKABE_ITO, TOL_MUTED, VARIANT_D];

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
    hint: 'Chosen for max ΔE under CVD against lime — distinct under deuteranopia (the two more saturated amber options collapse against lime).',
  },
  {
    key: 'neutral',
    hexLight: '#1A1A17',
    hexDark: '#F0EFE8',
    role: 'totals / baseline / outline',
    hint: 'Theme-adaptive ink. Same hex as text and gridlines — the series reads as part of the chart\'s structural layer.',
  },
  {
    key: 'muted',
    hexLight: '#6B6A63',
    hexDark: '#A8A79F',
    role: 'other / rest / disabled',
    hint: 'Theme-adaptive ink-muted. For "other" / "rest" slices, disabled series, confidence-band fills.',
  },
];

const HYBRID_V3_CVD: number[] = [36.19, 16.34, 13.98, 13.98, 13.70, 10.70, 8.81];
const PURE_CVD_GREEDY: number[] = [36.19, 21.45, 19.81, 15.20, 13.70, 10.70, 8.81];

function verdictFor(de: number): 'safe' | 'borderline' | 'fail' {
  if (de >= 14) return 'safe';
  if (de >= 10) return 'borderline';
  return 'fail';
}

const WCAG_TABLE: { hex: string; name: string; light: number; dark: number }[] = [
  { hex: '#009E73', name: 'brand-green', light: 3.08,  dark: 5.48 },
  { hex: '#AE3030', name: 'matte-red',   light: 5.79,  dark: 2.92 },
  { hex: '#C475FD', name: 'lavender',    light: 2.59,  dark: 6.53 },
  { hex: '#99B314', name: 'lime',        light: 2.15,  dark: 7.87 },
  { hex: '#4467A3', name: 'blue',        light: 5.09,  dark: 3.32 },
  { hex: '#2ABCCD', name: 'cyan',        light: 2.06,  dark: 8.19 },
  { hex: '#954477', name: 'rose',        light: 5.61,  dark: 3.01 },
  { hex: '#BD8233', name: 'ochre',       light: 2.95,  dark: 5.72 },
  { hex: '#DDCC77', name: 'amber',       light: 1.46,  dark: 11.59 },
];

type HistoryEntry = {
  id: string;
  title: string;
  date: string;
  hexes: string[];
  summary: string;
  href?: string;
  hrefLabel?: string;
};

const HISTORY: HistoryEntry[] = [
  {
    id: 'v3',
    title: 'v3 — imprint (current)',
    date: '2026',
    hexes: ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD', '#954477', '#99B314'],
    summary: '8 hues with first 4 slots from distinct hue families; semantic-red deferred to slot 4 so it stays a free anchor for bad / loss / error. Plus 3 anchors outside the pool (amber, neutral, muted).',
  },
  {
    id: 'v2',
    title: 'v2 — D1-8 (8-hex expansion)',
    date: '2026',
    hexes: ['#009E73', '#AE3030', '#C475FD', '#99B314', '#4467A3', '#2ABCCD', '#954477', '#BD8233'],
    summary: 'Eight-hex expansion of variant D. Picked over a vivid-8 alternative by 5 expert reviewers — muted and CVD-safe, but had two greens and two purples next to each other in the canonical order.',
  },
  {
    id: 'v1',
    title: 'v1 — variant D ("balanced")',
    date: 'May 2026',
    hexes: ['#009E73', '#9418DB', '#B71D27', '#16B8F3', '#99B314', '#D359A7', '#BA843E'],
    summary: 'anyplot\'s first custom palette. 7 hues + adaptive neutral. Brand green inherited from Okabe-Ito; positions 2–7 from a Petroff-style max-min ΔE search in the muted-paper chroma envelope.',
    href: 'https://arxiv.org/abs/2107.02270',
    hrefLabel: 'Petroff 2021 (arXiv)',
  },
  {
    id: 'v0',
    title: 'v0 — Okabe-Ito',
    date: '2002 / 2011',
    hexes: ['#009E73', '#D55E00', '#0072B2', '#CC79A7', '#E69F00', '#56B4E9', '#F0E442'],
    summary: 'The original colorblind-safe categorical palette (Wong 2011, Nature Methods). 7 hues + adaptive neutral, brand green at slot 0.',
    href: 'https://jfly.uni-koeln.de/color/',
    hrefLabel: 'jfly.uni-koeln.de',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Code snippets per language
// ─────────────────────────────────────────────────────────────────────────────

type Lang = 'python' | 'r' | 'julia' | 'js';
const LANG_LABELS: Record<Lang, string> = {
  python: 'Python', r: 'R', julia: 'Julia', js: 'JavaScript',
};

function snippet(lang: Lang, oklch: boolean, sortedPalette: Swatch[]): string {
  const values = oklch ? sortedPalette.map(s => s.oklch) : sortedPalette.map(s => s.hex);
  const amberVal = oklch ? 'oklch(0.841 0.108 98.3)' : '#DDCC77';
  const seqStart = oklch ? 'oklch(0.620 0.130 165.5)' : '#009E73';
  const seqEnd   = oklch ? 'oklch(0.516 0.104 260.6)' : '#4467A3';
  const divStart = oklch ? 'oklch(0.503 0.163 25.2)' : '#AE3030';
  const divEnd   = oklch ? 'oklch(0.516 0.104 260.6)' : '#4467A3';
  switch (lang) {
    case 'python':
      return `ANYPLOT_PALETTE = [
${values.map(v => `    "${v}"`).join(',\n')},
]
ANYPLOT_AMBER = "${amberVal}"  # warning / caution

# first series is ALWAYS slot 0 (brand green)
color = ANYPLOT_PALETTE[0]

# continuous data — sequential + diverging cmaps
from matplotlib.colors import LinearSegmentedColormap
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["${seqStart}", "${seqEnd}"])
midpoint = "#F5F3EC" if THEME == "light" else "#1A1A17"  # theme-adaptive
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["${divStart}", midpoint, "${divEnd}"])`;
    case 'r':
      return `ANYPLOT_PALETTE <- c(
${values.map(v => `  "${v}"`).join(',\n')}
)
ANYPLOT_AMBER <- "${amberVal}"  # warning / caution

# first series is ALWAYS slot 0 (brand green)
color <- ANYPLOT_PALETTE[1]

# continuous data — ggplot2 gradient scales
midpoint <- if (theme == "light") "#F5F3EC" else "#1A1A17"
scale_color_gradient(low = "${seqStart}", high = "${seqEnd}")                         # sequential
scale_color_gradient2(low = "${divStart}", mid = midpoint, high = "${divEnd}", midpoint = 0)  # diverging`;
    case 'julia':
      return `const ANYPLOT_PALETTE = [
${values.map(v => oklch ? `    "${v}"` : `    colorant"${v}"`).join(',\n')},
]
const ANYPLOT_AMBER = ${oklch ? `"${amberVal}"` : `colorant"${amberVal}"`}  # warning

# first series is ALWAYS slot 0 (brand green)
color = ANYPLOT_PALETTE[1]

# continuous data — Makie cgrad
using ColorSchemes
midpoint = theme == "light" ? colorant"#F5F3EC" : colorant"#1A1A17"
const ANYPLOT_SEQ = cgrad([colorant"${seqStart}", colorant"${seqEnd}"])
const ANYPLOT_DIV = cgrad([colorant"${divStart}", midpoint, colorant"${divEnd}"])`;
    case 'js':
      return `const ANYPLOT_PALETTE = [
${values.map(v => `  "${v}"`).join(',\n')},
];
const ANYPLOT_AMBER = "${amberVal}"; // warning / caution

// first series is ALWAYS slot 0 (brand green)
const color = ANYPLOT_PALETTE[0];

// continuous data — two-stop / three-stop gradients
const midpoint = theme === "light" ? "#F5F3EC" : "#1A1A17"; // theme-adaptive
const IMPRINT_SEQ = [[0, "${seqStart}"], [1, "${seqEnd}"]];
const IMPRINT_DIV = [[0, "${divStart}"], [0.5, midpoint], [1, "${divEnd}"]];`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Inline sub-components
// ─────────────────────────────────────────────────────────────────────────────

const MAX_WHEEL_CHROMA = 0.28; // clamp for radial position normalisation across palettes

type WheelDot = { hex: string; L: number; C: number; H: number };

/** Pick a readable text color (ink-dark or ink-light) for a hex bg via WCAG luminance. */
function textOn(hex: string): string {
  const s = hex.replace('#', '');
  const r = parseInt(s.slice(0, 2), 16) / 255;
  const g = parseInt(s.slice(2, 4), 16) / 255;
  const b = parseInt(s.slice(4, 6), 16) / 255;
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return L > 0.5 ? '#1A1A17' : '#F0EFE8';
}

function ChromaWheel({
  size = 320,
  imprintDots,
  overlay,
}: {
  size?: number;
  imprintDots: WheelDot[];
  overlay?: WheelDot[];
}) {
  const cx = size / 2;
  const cy = size / 2;
  const outerR = (size / 2) - 12;
  const dotR = 8;

  // Project (hue°, chroma) → (x, y). Hue 0° at right (3 o'clock), increment CCW
  // so the resulting layout matches the CSS conic-gradient ring rendered below.
  const project = (H: number, C: number): { x: number; y: number } => {
    const rad = (H * Math.PI) / 180;
    const r = Math.min(C / MAX_WHEEL_CHROMA, 1) * outerR;
    return {
      x: cx + Math.cos(rad) * r,
      y: cy - Math.sin(rad) * r, // negate because screen y grows downward
    };
  };

  // Build the conic gradient OKLCH stops every 15° so the wheel reads as a
  // proper colour wheel. CSS conic-gradient starts at 12 o'clock and goes
  // clockwise, but our hue convention has 0° at 3 o'clock going counter-
  // clockwise (sin/cos math). Map: cssAngle = (90 - hue + 360) mod 360.
  const gradStops = Array.from({ length: 25 }, (_, i) => {
    const cssAngle = i * 15;
    const hue = (90 - cssAngle + 360) % 360;
    return `oklch(0.72 0.18 ${hue}deg) ${cssAngle}deg`;
  }).join(', ');

  return (
    <Box sx={{ position: 'relative', width: size, height: size }}>
      {/* Hue ring background (CSS conic-gradient + radial-gradient overlay for chroma fade to centre) */}
      <Box
        sx={{
          position: 'absolute', inset: 0,
          borderRadius: '50%',
          background: `
            radial-gradient(circle at center, var(--bg-page) 0%, var(--bg-page) 8%, transparent 60%),
            conic-gradient(from 0deg, ${gradStops})
          `,
          // soft outer ring so the wheel reads as a contained object on cream bg
          boxShadow: 'inset 0 0 0 1px var(--rule)',
        }}
      />
      {/* SVG overlay — dots */}
      <Box component="svg" viewBox={`0 0 ${size} ${size}`} sx={{ position: 'absolute', inset: 0 }}>
        {/* Overlay palette (hollow rings) — render BELOW imprint dots so imprint stays visually dominant */}
        {overlay && overlay.map((d, i) => {
          const { x, y } = project(d.H, d.C);
          return (
            <circle
              key={`o-${i}`}
              cx={x} cy={y} r={dotR - 1}
              fill="none"
              stroke={d.hex}
              strokeWidth={2.5}
              opacity={0.95}
            />
          );
        })}
        {/* Imprint dots (filled) */}
        {imprintDots.map((d, i) => {
          const { x, y } = project(d.H, d.C);
          return (
            <g key={i}>
              <circle
                cx={x} cy={y} r={dotR}
                fill={d.hex}
                stroke={i === 0 ? 'var(--ink)' : 'var(--bg-page)'}
                strokeWidth={i === 0 ? 2 : 1.2}
              />
            </g>
          );
        })}
      </Box>
    </Box>
  );
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <Box sx={{ position: 'relative', mt: 2 }}>
      <Box
        component="pre"
        sx={{
          fontFamily: typography.mono,
          fontSize: '12px',
          lineHeight: 1.6,
          color: 'var(--code-text)',
          backgroundColor: 'var(--code-bg)',
          border: '1px solid var(--rule)',
          borderRadius: 1,
          p: 2,
          pr: 6,
          overflowX: 'auto',
          margin: 0,
          whiteSpace: 'pre',
        }}
      >
        {code}
      </Box>
      <Tooltip title={copied ? 'copied' : 'copy'} placement="left">
        <IconButton
          size="small"
          onClick={handleCopy}
          sx={{
            position: 'absolute', top: 6, right: 6,
            color: copied ? colors.primary : 'var(--ink-muted)',
          }}
        >
          <ContentCopyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

function CollapsibleSection({ title, defaultOpen = false, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Box sx={{ borderTop: '1px solid var(--rule)', pt: 2 }}>
      <Box
        component="button"
        onClick={() => setOpen(o => !o)}
        sx={{
          width: '100%',
          display: 'flex', alignItems: 'center', gap: 1,
          background: 'none', border: 'none', cursor: 'pointer',
          fontFamily: typography.mono,
          fontSize: '13px',
          color: 'var(--ink)',
          py: 1,
          textAlign: 'left',
        }}
      >
        <ExpandMoreIcon sx={{ transition: 'transform 0.2s', transform: open ? 'rotate(0deg)' : 'rotate(-90deg)', fontSize: '20px', color: 'var(--ink-muted)' }} />
        {title}
      </Box>
      <Collapse in={open}>
        <Box sx={{ pb: 2, pt: 1 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}

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
  const [lang, setLang] = useState<Lang>('python');
  const [oklch, setOklch] = useState(false);
  const [compareId, setCompareId] = useState<string | null>(null);
  /** `imprint` = hybrid-v3 (default, 4 hue families up front).
   *  `cvd` = pure-CVD-greedy max-min (best per-n ΔE under CVD, but groups
   *  two greens + two purples close together in the first 4 slots). */
  const [sort, setSort] = useState<'imprint' | 'cvd'>('imprint');
  // legacy state retained but no longer wired to a toggle — the per-n table
  // now always shows both sortings side-by-side so the trade-off is visible
  // without an extra UI control.

  useEffect(() => {
    trackPageview('/palette');
  }, [trackPageview]);

  const sortedPalette: Swatch[] = useMemo(
    () => (sort === 'imprint' ? PALETTE : CVD_OPTIMAL_ORDER.map(i => PALETTE[i])),
    [sort]
  );
  const sortedHexes = useMemo(() => sortedPalette.map(s => s.hex), [sortedPalette]);

  // Wheel dots are positioned by hue + chroma, independent of sort order —
  // we keep the canonical PALETTE order so the brand-green outline stays on
  // the same identity dot regardless of sort.
  const imprintDots: WheelDot[] = useMemo(
    () => PALETTE.map(s => ({ hex: s.hex, L: s.L, C: s.C, H: s.H })),
    []
  );
  const overlayDots: WheelDot[] | undefined = useMemo(
    () => COMPARISONS.find(c => c.id === compareId)?.hexes,
    [compareId]
  );

  return (
    <>
      <Helmet>
        <title>palette | anyplot.ai</title>
        <meta name="description" content="The anyplot imprint palette — 8 colorblind-safe categorical hues plus 3 semantic anchors (amber, neutral, muted). Tuned for warm-paper rendering, validated against deuteranopia / protanopia / tritanopia." />
        <link rel="canonical" href="https://anyplot.ai/palette" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* 1. HERO */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>imprint</em>} />
          <Box sx={{ ...proseColumnSx, display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 400px' }, gap: 4, alignItems: 'center', mt: 3 }}>
            <Box>
              <Box sx={textStyle}>
                every plot on anyplot uses <strong>imprint</strong>, a categorical palette of 8 colours plus 3
                semantic anchors. low-chroma, warm-tinted for cream paper, validated against
                deuteranopia / protanopia / tritanopia. designed to be easier on the eyes and let the data
                speak — same neighbourhood as palettes that have shipped at scale in scientific publishing and
                editorial dashboards.
              </Box>
              <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)', mt: 2 }}>
                compare with other categorical palettes:
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {COMPARISONS.map((c) => {
                  const active = compareId === c.id;
                  return (
                    <Box
                      key={c.id}
                      component="button"
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
                      {/* Mini swatch strip for the comparison palette */}
                      <Box sx={{ display: 'flex', borderRadius: 0.5, overflow: 'hidden', boxShadow: '0 0 0 1px var(--rule)' }}>
                        {c.hexes.map((d) => (
                          <Box key={d.hex} sx={{ width: 8, height: 14, bgcolor: d.hex }} />
                        ))}
                      </Box>
                      {c.name}
                    </Box>
                  );
                })}
              </Box>
            </Box>
            <Box sx={{ justifySelf: { xs: 'center', md: 'end' } }}>
              <ChromaWheel size={380} imprintDots={imprintDots} overlay={overlayDots} />
              <Box sx={{ fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)', textAlign: 'center', mt: 1 }}>
                hue clockwise · chroma = distance from centre
                {compareId && (
                  <Box component="span" sx={{ display: 'block', mt: 0.5 }}>
                    rings = {COMPARISONS.find(c => c.id === compareId)?.name}
                  </Box>
                )}
              </Box>
            </Box>
          </Box>
          <Box sx={{ mt: 4 }}>
            <PaletteStrip maxWidth={null} height={48} mt={0} hexes={sortedHexes} />
          </Box>
        </Box>

        {/* 2. COMPACT PALETTE GRID + SORT TOGGLE */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>the 8 categorical hues</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mt: 1, mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>
                sort:
                {(['imprint', 'cvd'] as const).map((s) => (
                  <Box
                    key={s}
                    component="button"
                    onClick={() => setSort(s)}
                    sx={{
                      background: 'none', border: 'none', padding: 0, ml: 1,
                      fontFamily: typography.mono, fontSize: '11px',
                      color: sort === s ? colors.primary : 'var(--ink-soft)',
                      textDecoration: 'underline',
                      textDecorationColor: sort === s ? colors.primary : 'var(--rule)',
                      cursor: 'pointer',
                    }}
                  >
                    {s === 'imprint' ? 'imprint (default)' : 'CVD-optimal (max ΔE under colorblindness)'}
                  </Box>
                ))}
              </Box>
            </Box>
            {sort === 'cvd' && (
              <Box sx={{ fontSize: '11px', color: 'var(--ink-muted)', fontFamily: typography.mono, lineHeight: 1.55, mb: 2, p: 1.5, borderLeft: `2px solid ${colors.primary}`, backgroundColor: 'var(--bg-surface)' }}>
                pure max-min sort — best ΔE under deuteranopia / protanopia (n=3..4 goes from 16.34 → 21.45 and
                13.98 → 19.81). but the first 4 slots end up with two greens (brand + lime) and two purples
                (lavender + rose) side by side. copy this set if your audience is CVD-first and small-n;
                imprint default is the better balance for general use.
              </Box>
            )}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(4, 1fr)', md: 'repeat(8, 1fr)' }, gap: 1 }}>
              {sortedPalette.map((s, i) => (
                <Box key={s.hex} sx={{ display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{
                    height: 72,
                    bgcolor: s.hex,
                    color: textOn(s.hex),
                    display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
                    pb: 0.5,
                    fontFamily: typography.mono, fontSize: '10px',
                    borderRadius: 1,
                    boxShadow: i === 0 ? `inset 0 0 0 2px var(--ink)` : 'inset 0 0 0 1px var(--rule)',
                  }}>
                    {s.hex}
                  </Box>
                  <Box sx={{
                    fontFamily: typography.mono, fontSize: '9px',
                    textAlign: 'center',
                    mt: 0.5,
                    lineHeight: 1.4,
                  }}>
                    <Box sx={{ color: 'var(--ink)', fontWeight: 600 }}>slot {i}{i === 0 ? ' ★' : ''}</Box>
                    <Box sx={{ color: 'var(--ink)' }}>{s.name}</Box>
                    <Box sx={{ color: 'var(--ink-muted)', mt: 0.5 }}>{s.role}</Box>
                    <Box sx={{ color: 'var(--ink-muted)', mt: 0.5 }}>H={s.H.toFixed(0)}°</Box>
                    <Tooltip title="min ΔE to any other slot — normal vision">
                      <Box sx={{ color: 'var(--ink-muted)', mt: 0.5, display: 'inline-block', cursor: 'help' }}>
                        norm <Box component="span" sx={{ color: 'var(--ink)' }}>{s.minNorm.toFixed(1)}</Box>
                      </Box>
                    </Tooltip>
                    <Box sx={{ color: 'var(--ink-muted)' }}> · </Box>
                    <Tooltip title="min ΔE to any other slot — worst of deuteranopia / protanopia / tritanopia">
                      <Box sx={{ color: 'var(--ink-muted)', display: 'inline-block', cursor: 'help' }}>
                        cvd <Box component="span" sx={{ color: 'var(--ink)' }}>{s.minCvd.toFixed(1)}</Box>
                      </Box>
                    </Tooltip>
                    <Box sx={{ color: 'var(--ink-muted)', mt: 0.5 }}>
                      <Tooltip title="WCAG contrast on cream bg (#F5F3EC) — graphical objects 3:1 minimum">
                        <Box component="span" sx={{ color: s.wcagL >= 3 ? '#007A59' : '#b62d2d', cursor: 'help' }}>
                          ☼ {s.wcagL.toFixed(1)}
                        </Box>
                      </Tooltip>
                      {' / '}
                      <Tooltip title="WCAG contrast on dark bg (#121210)">
                        <Box component="span" sx={{ color: s.wcagD >= 3 ? '#007A59' : '#b62d2d', cursor: 'help' }}>
                          ☽ {s.wcagD.toFixed(1)}
                        </Box>
                      </Tooltip>
                    </Box>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>

        {/* 3. SEMANTIC ANCHORS */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>semantic anchors</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              three additional anchors that live <strong>outside</strong> the categorical pool. they are never
              returned by <code>palette[:n]</code> — reached only by name. two of them flip per theme.
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mt: 2 }}>
              {ANCHORS.map((a) => (
                <Box key={a.key} sx={{ border: '1px solid var(--rule)', borderRadius: 2, overflow: 'hidden', backgroundColor: 'var(--bg-surface)' }}>
                  {a.hexDark ? (
                    <Box sx={{ height: 56, display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
                      <Box sx={{ bgcolor: a.hexLight, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', pb: 0.5, color: '#F0EFE8', fontFamily: typography.mono, fontSize: '10px' }}>
                        {a.hexLight}
                      </Box>
                      <Box sx={{ bgcolor: a.hexDark, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', pb: 0.5, color: '#1A1A17', fontFamily: typography.mono, fontSize: '10px' }}>
                        {a.hexDark}
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ height: 56, bgcolor: a.hexLight }} />
                  )}
                  <Box sx={{ p: 1.5 }}>
                    <Box sx={{ fontFamily: typography.mono, fontSize: '11px', fontWeight: 600, color: 'var(--ink)', mb: 0.5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {a.role}
                    </Box>
                    <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)', mb: 0.75 }}>
                      palette.{a.key}{a.hexDark ? ' — adaptive' : ''}
                    </Box>
                    <Box sx={{ fontSize: '12px', color: 'var(--ink-muted)', lineHeight: 1.5 }}>
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
              for continuous data the categorical pool is replaced with two palette-derived colormaps. no
              other cmap is used — not viridis, not jet, not rainbow.
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mt: 2 }}>
              {/* Sequential */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mb: 0.5 }}>
                  <Box sx={{ fontFamily: typography.mono, fontSize: '12px', fontWeight: 600, color: 'var(--ink)' }}>
                    imprint_seq
                  </Box>
                  <Box sx={{ fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)' }}>
                    single-polarity · density / magnitude
                  </Box>
                </Box>
                <Box sx={{
                  height: 28,
                  borderRadius: 1,
                  background: 'linear-gradient(to right, #009E73, #4467A3)',
                  boxShadow: '0 0 0 1px var(--rule)',
                }} />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5, fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)' }}>
                  <span>#009E73 brand-green</span>
                  <span>#4467A3 blue</span>
                </Box>
              </Box>
              {/* Diverging */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mb: 0.5 }}>
                  <Box sx={{ fontFamily: typography.mono, fontSize: '12px', fontWeight: 600, color: 'var(--ink)' }}>
                    imprint_div
                  </Box>
                  <Box sx={{ fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)' }}>
                    diverging · correlations / signed deviations
                  </Box>
                </Box>
                <Box sx={{
                  height: 28,
                  borderRadius: 1,
                  background: 'linear-gradient(to right, #AE3030, #F5F3EC, #4467A3)',
                  boxShadow: '0 0 0 1px var(--rule)',
                }} />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5, fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)' }}>
                  <span>#AE3030 red</span>
                  <span style={{ color: 'var(--ink-muted)' }}>theme-adaptive midpoint</span>
                  <span>#4467A3 blue</span>
                </Box>
              </Box>
            </Box>
            <Box sx={{ fontSize: '11px', color: 'var(--ink-muted)', mt: 2, fontFamily: typography.mono, lineHeight: 1.55 }}>
              the diverging midpoint flips per theme — <code>#F5F3EC</code> on cream bg / <code>#1A1A17</code>
              on warm-near-black — so the zero point reads as part of the page rather than as a grey blob.
            </Box>
          </Box>
        </Box>

        {/* 4. COPY SNIPPETS */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>copy &amp; paste</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2, mt: 2 }}>
              <Tabs
                value={lang}
                onChange={(_, v) => setLang(v as Lang)}
                variant="scrollable"
                scrollButtons="auto"
                sx={{
                  minHeight: 36,
                  '& .MuiTab-root': { fontFamily: typography.mono, fontSize: '11px', minHeight: 36, py: 0, textTransform: 'none', color: 'var(--ink-muted)' },
                  '& .Mui-selected': { color: 'var(--ink)' },
                  '& .MuiTabs-indicator': { backgroundColor: colors.primary },
                }}
              >
                {(Object.keys(LANG_LABELS) as Lang[]).map(l => (
                  <Tab key={l} value={l} label={LANG_LABELS[l]} />
                ))}
              </Tabs>
              <FormControlLabel
                control={<Switch size="small" checked={oklch} onChange={(e) => setOklch(e.target.checked)} sx={{ '& .MuiSwitch-switchBase.Mui-checked': { color: colors.primary }, '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: colors.primary } }} />}
                label={<Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>OKLCH</Box>}
              />
            </Box>
            <CodeBlock code={snippet(lang, oklch, sortedPalette)} />
          </Box>
        </Box>

        {/* 5. CVD SAFETY */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>best variant for CVD users</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              the imprint sort holds worst-pair ΔE under simulated deuteranopia / protanopia / tritanopia above
              the 10-point discrimination floor through <strong>n = 6</strong>. beyond that the eye starts
              losing pairs — add a marker shape or linestyle.
            </Box>
            <Box sx={{ overflowX: 'auto', mt: 2 }}>
              <Box component="table" sx={{
                width: '100%',
                borderCollapse: 'collapse',
                fontFamily: typography.mono,
                fontSize: '11px',
                '& th, & td': { padding: '6px 12px', textAlign: 'left', borderBottom: '1px solid var(--rule)' },
                '& th': { color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' },
                '& td.num': { textAlign: 'right', color: 'var(--ink)' },
              }}>
                <thead>
                  <tr>
                    <th>n series</th>
                    <th style={{ textAlign: 'right' }}>imprint (default)</th>
                    <th style={{ textAlign: 'right' }}>CVD-optimal sort</th>
                    <th>verdict (imprint)</th>
                  </tr>
                </thead>
                <tbody>
                  {HYBRID_V3_CVD.map((de, i) => {
                    const verdict = verdictFor(de);
                    const altDe = PURE_CVD_GREEDY[i];
                    return (
                      <tr key={i}>
                        <td>{i + 2}</td>
                        <td className="num">{de.toFixed(2)}</td>
                        <td className="num" style={{ color: altDe > de ? '#007A59' : 'var(--ink-muted)' }}>
                          {altDe.toFixed(2)}{altDe > de ? ' ↑' : altDe < de ? ' ↓' : ' ='}
                        </td>
                        <td style={{
                          color: verdict === 'safe' ? '#007A59' : verdict === 'borderline' ? '#b56b18' : '#b62d2d',
                          fontWeight: 600,
                        }}>{verdict}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </Box>
            </Box>
            <Box sx={{ fontSize: '11px', color: 'var(--ink-muted)', mt: 2, fontFamily: typography.mono, lineHeight: 1.55 }}>
              the CVD-optimal sort is technically better at n=3..4 but groups two greens and two purples in
              the first 4 slots. imprint trades a few ΔE points for visually distinct hue families up front —
              the n=8 floor (8.81) is identical because both sortings ship the same 8 hexes. swap to it via
              the sort toggle above if your audience is CVD-first.
            </Box>
          </Box>
        </Box>

        {/* 6. WCAG AUDIT (collapsible) */}
        <Box component="section" sx={sectionSx}>
          <Box sx={proseColumnSx}>
            <CollapsibleSection title="WCAG contrast on both themes (and the outline pattern)">
              <Box sx={textStyle}>
                muted palettes share a known limit: the lighter members carry their distinguishability through
                chroma, not L-spread. On cream bg <code>#F5F3EC</code>, five categorical hues + amber fall under
                WCAG 2.1 SC 1.4.11&apos;s 3:1 minimum. The industry-standard fix is a <strong>1px ink-color
                stroke</strong> on affected series — but it&apos;s a renderer judgment call, not a hard rule.
              </Box>
              <Box sx={{ mt: 2, overflowX: 'auto' }}>
                <Box component="table" sx={{
                  width: '100%', borderCollapse: 'collapse',
                  fontFamily: typography.mono, fontSize: '11px',
                  '& th, & td': { padding: '6px 12px', textAlign: 'left', borderBottom: '1px solid var(--rule)' },
                  '& th': { color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' },
                }}>
                  <thead>
                    <tr>
                      <th>hex</th>
                      <th>name</th>
                      <th style={{ textAlign: 'right' }}>on cream</th>
                      <th style={{ textAlign: 'right' }}>on dark</th>
                    </tr>
                  </thead>
                  <tbody>
                    {WCAG_TABLE.map((row) => (
                      <tr key={row.hex}>
                        <td>
                          <Box component="span" sx={{ display: 'inline-block', width: 12, height: 12, borderRadius: 2, bgcolor: row.hex, mr: 1, verticalAlign: 'middle', border: '1px solid var(--rule)' }} />
                          {row.hex}
                        </td>
                        <td style={{ color: 'var(--ink-muted)' }}>{row.name}</td>
                        <td style={{ textAlign: 'right', color: row.light < 3 ? '#b62d2d' : '#007A59', fontWeight: 600 }}>
                          {row.light.toFixed(2)}:1 {row.light < 3 ? '✗' : '✓'}
                        </td>
                        <td style={{ textAlign: 'right', color: row.dark < 3 ? '#b62d2d' : '#007A59', fontWeight: 600 }}>
                          {row.dark.toFixed(2)}:1 {row.dark < 3 ? '✗' : '✓'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>

        {/* 7. HISTORY (collapsible) */}
        <Box component="section" sx={sectionSx}>
          <Box sx={proseColumnSx}>
            <CollapsibleSection title="palette history — how we got here">
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
                {HISTORY.map((entry) => (
                  <Box key={entry.id}>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mb: 1, flexWrap: 'wrap' }}>
                      <Box sx={{ fontFamily: typography.mono, fontSize: '13px', color: 'var(--ink)', fontWeight: 600 }}>
                        {entry.title}
                      </Box>
                      <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>
                        {entry.date}
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
                    <Box sx={{ display: 'flex', mb: 1, borderRadius: 1, overflow: 'hidden', boxShadow: '0 0 0 1px var(--rule)' }}>
                      {entry.hexes.map((hx) => (
                        <Box key={hx} sx={{ flex: 1, height: 32, bgcolor: hx }} title={hx} />
                      ))}
                    </Box>
                    <Box sx={{ fontSize: '12px', color: 'var(--ink-muted)', lineHeight: 1.55 }}>
                      {entry.summary}
                    </Box>
                  </Box>
                ))}
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>
      </Box>
    </>
  );
}
