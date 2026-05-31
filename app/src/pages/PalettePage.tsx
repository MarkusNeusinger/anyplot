import { useEffect, useMemo, useRef, useState } from 'react';
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
import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { colors, typography, textStyle } from '../theme';
import matrixData from '../data/paletteMatrices.json';

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
  /** WCAG contrast on cream bg #FAF8F1. */
  wcagL: number;
  /** WCAG contrast on warm near-black bg #121210. */
  wcagD: number;
};

export const PALETTE: Swatch[] = [
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
    { hex: '#B3B3B3', L: 0.767, C: 0.000, H: 89.9 },
  ],
};

const ANYPLOT_PREV: CompPalette = {
  id: 'prev',
  name: 'anyplot v1 (previous live)',
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

const COMPARISONS: CompPalette[] = [OKABE_ITO, TOL_MUTED, SET2, ANYPLOT_PREV];

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
  hexes: string[];
  summary: string;
  href?: string;
  hrefLabel?: string;
};

const HISTORY: HistoryEntry[] = [
  {
    id: 'v3',
    title: 'v3 — imprint (current)',
    hexes: ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD', '#954477', '#99B314'],
    summary: '8 hues; the first four come from distinct hue families and stay above the 10-ΔE discrimination floor under CVD (worst pair 13.98 at n=4). Semantic red is deferred to slot 4 so it stays a free anchor for bad / loss / error instead of appearing in every 3-series chart. Plus 3 anchors outside the pool (amber, neutral, muted).',
  },
  {
    id: 'v2',
    title: 'v2 — D1-8 (internal · never shipped)',
    hexes: ['#009E73', '#AE3030', '#C475FD', '#99B314', '#4467A3', '#2ABCCD', '#954477', '#BD8233'],
    summary: 'A work-in-progress step on the way to v3 — never released; v1 stayed live throughout. This is where the 8-hex muted set was locked in, chosen over a higher-chroma vivid-8 whose CVD-distance edge was marginal (n=4: 17.3 vs 15.2 ΔE) and below the ~10-ΔE discrimination floor at n=8 anyway, while the muted register reads editorial rather than dashboard. The colours were right but the slot order was not — a pure-CVD-greedy sort put two greens and two purples in the first four slots. That ordering fix is exactly what v3 added, so v2 went straight to v3 without a live release.',
  },
  {
    id: 'v1',
    title: 'v1 — variant D ("balanced")',
    hexes: ['#009E73', '#9418DB', '#B71D27', '#16B8F3', '#99B314', '#D359A7', '#BA843E'],
    summary: 'anyplot\'s first custom palette, and the last one shipped before v3 — v2 never went live, so this is what "anyplot v1 (previous live)" overlays on the wheel above. 7 hues + adaptive neutral. Brand green inherited from Okabe-Ito; the rest from a Petroff-style max-min ΔE search in the muted-paper chroma envelope — separating red from tan and trading the near-yellow for olive-lime so nothing washes out on cream.',
    href: 'https://arxiv.org/abs/2107.02270',
    hrefLabel: 'Petroff 2021 (arXiv)',
  },
  {
    id: 'v0',
    title: 'v0 — Okabe-Ito',
    hexes: ['#009E73', '#D55E00', '#0072B2', '#CC79A7', '#E69F00', '#56B4E9', '#F0E442'],
    summary: 'The original colorblind-safe categorical palette (Wong 2011, Nature Methods). 7 hues + adaptive neutral, brand green at slot 0 — inherited unchanged by every version since. Its limits on warm paper: orange and vermillion sit only ~25° apart on the hue wheel, and the yellow washes out on cream — both fixed by the later variants.',
    href: 'https://jfly.uni-koeln.de/color/',
    hrefLabel: 'jfly.uni-koeln.de',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Code snippets per language
// ─────────────────────────────────────────────────────────────────────────────

export type Lang = 'python' | 'r' | 'julia' | 'js';
const LANG_LABELS: Record<Lang, string> = {
  python: 'Python', r: 'R', julia: 'Julia', js: 'JavaScript',
};

export function snippet(lang: Lang, oklch: boolean, sortedPalette: Swatch[]): string {
  // CSS `oklch()` literals are only consumable where the runtime parses CSS
  // colours (JS / CSS). matplotlib, ggplot2 and Makie can't read them, so those
  // snippets stay hex (runnable) and surface the OKLCH coordinate as a trailing
  // comment instead — toggling OKLCH then annotates rather than breaks the code.
  const useLiteral = oklch && lang === 'js';
  const colorVal = (s: Swatch) => (useLiteral ? s.oklch : s.hex);
  const hueComment = (s: Swatch) => (oklch && lang !== 'js' ? `  # ${s.oklch}` : '');
  const amberVal = useLiteral ? 'oklch(0.841 0.108 98.3)' : '#DDCC77';
  const seqStart = useLiteral ? 'oklch(0.620 0.130 165.5)' : '#009E73';
  const seqEnd   = useLiteral ? 'oklch(0.516 0.104 260.6)' : '#4467A3';
  const divStart = useLiteral ? 'oklch(0.503 0.163 25.2)' : '#AE3030';
  const divEnd   = useLiteral ? 'oklch(0.516 0.104 260.6)' : '#4467A3';
  // Theme-adaptive neutrals + diverging midpoints are kept as hex in both
  // modes — they are structural near-greys, and converting them to OKLCH adds
  // noise without helping anyone paste them.
  switch (lang) {
    case 'python':
      return `from types import SimpleNamespace

# imprint — anyplot's palette (https://anyplot.ai/palette)
IMPRINT = SimpleNamespace(
    hues=[
${sortedPalette.map(s => `        "${s.hex}",${hueComment(s)}`).join('\n')}
    ],
    amber="${amberVal}",  # warning / caution
    neutral=SimpleNamespace(light="#1A1A17", dark="#F0EFE8"),
    muted=SimpleNamespace(light="#6B6A63", dark="#A8A79F"),
    seq=["${seqStart}", "${seqEnd}"],  # sequential: green -> blue
    div=SimpleNamespace(               # diverging: red <-> midpoint <-> blue
        light=["${divStart}", "#FAF8F1", "${divEnd}"],
        dark=["${divStart}", "#1A1A17", "${divEnd}"],
    ),
)

color = IMPRINT.hues[0]  # first series is ALWAYS slot 0 (brand green)

# continuous data — build matplotlib cmaps from the stops
from matplotlib.colors import LinearSegmentedColormap
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", IMPRINT.seq)
imprint_div = LinearSegmentedColormap.from_list("imprint_div", IMPRINT.div.light)  # .dark on dark bg`;
    case 'r':
      return `# imprint — anyplot's palette (https://anyplot.ai/palette)
IMPRINT <- list(
  hues = c(
${sortedPalette.map((s, i, arr) => `    "${s.hex}"${i < arr.length - 1 ? ',' : ''}${hueComment(s)}`).join('\n')}
  ),
  amber = "${amberVal}",  # warning / caution
  neutral = list(light = "#1A1A17", dark = "#F0EFE8"),
  muted   = list(light = "#6B6A63", dark = "#A8A79F"),
  seq = c("${seqStart}", "${seqEnd}"),  # sequential: green -> blue
  div = list(                           # diverging: red <-> midpoint <-> blue
    light = c("${divStart}", "#FAF8F1", "${divEnd}"),
    dark  = c("${divStart}", "#1A1A17", "${divEnd}")
  )
)

color <- IMPRINT$hues[1]  # first series is ALWAYS slot 0 (brand green)

# continuous data — ggplot2 gradient scales
scale_color_gradientn(colours = IMPRINT$seq)        # sequential
scale_color_gradientn(colours = IMPRINT$div$light)  # diverging (light theme)`;
    case 'julia':
      return `using Colors  # colorant"#..."

# imprint — anyplot's palette (https://anyplot.ai/palette)
const IMPRINT = (
    hues = [
${sortedPalette.map(s => `        colorant"${s.hex}",${hueComment(s)}`).join('\n')}
    ],
    amber = colorant"${amberVal}",  # warning / caution
    neutral = (light = colorant"#1A1A17", dark = colorant"#F0EFE8"),
    muted   = (light = colorant"#6B6A63", dark = colorant"#A8A79F"),
    seq = [colorant"${seqStart}", colorant"${seqEnd}"],
    div = (light = [colorant"${divStart}", colorant"#FAF8F1", colorant"${divEnd}"],
           dark  = [colorant"${divStart}", colorant"#1A1A17", colorant"${divEnd}"]),
)

color = IMPRINT.hues[1]  # first series is ALWAYS slot 0 (brand green)

# continuous data — Makie / ColorSchemes
using ColorSchemes
imprint_seq = cgrad(IMPRINT.seq)
imprint_div = cgrad(IMPRINT.div.light)  # .dark on dark bg`;
    case 'js':
      return `// imprint — anyplot's palette (https://anyplot.ai/palette)
const IMPRINT = {
  hues: [
${sortedPalette.map(s => `    "${colorVal(s)}",`).join('\n')}
  ],
  amber: "${amberVal}", // warning / caution
  neutral: { light: "#1A1A17", dark: "#F0EFE8" },
  muted:   { light: "#6B6A63", dark: "#A8A79F" },
  seq: ["${seqStart}", "${seqEnd}"], // sequential: green -> blue
  div: {                             // diverging: red <-> midpoint <-> blue
    light: ["${divStart}", "#FAF8F1", "${divEnd}"],
    dark:  ["${divStart}", "#1A1A17", "${divEnd}"],
  },
};

const color = IMPRINT.hues[0]; // first series is ALWAYS slot 0 (brand green)

// continuous data — [stop, color] pairs for your charting lib
const imprintSeq = IMPRINT.seq.map((c, i, a) => [i / (a.length - 1), c]);
const imprintDiv = IMPRINT.div.light.map((c, i, a) => [i / (a.length - 1), c]);`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Inline sub-components
// ─────────────────────────────────────────────────────────────────────────────

const MAX_WHEEL_CHROMA = 0.28; // clamp for radial position normalisation across palettes
const WHEEL_RING_L = 0.72;     // fixed OKLCH lightness for the hue-ring disk

type WheelDot = { hex: string; L: number; C: number; H: number };

/** OKLCH (L 0..1, C, H°) → sRGB [r,g,b] 0..255, clamped to gamut.
 *  Björn Ottosson's OKLab→linear-sRGB matrices. Used to paint the wheel disk
 *  per-pixel so the hue ring is seamless (no conic-gradient facets). */
function oklchToRgb(L: number, C: number, H: number): [number, number, number] {
  const h = (H * Math.PI) / 180;
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
  const l = l_ * l_ * l_;
  const m = m_ * m_ * m_;
  const s = s_ * s_ * s_;
  const lin = (c: number) => {
    const v = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
    return Math.max(0, Math.min(1, v));
  };
  const r = lin(+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
  const g = lin(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
  const bb = lin(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s);
  return [Math.round(r * 255), Math.round(g * 255), Math.round(bb * 255)];
}

/** 5-point star polygon points string, centred at (cx,cy). */
function starPoints(cx: number, cy: number, rOuter: number, rInner: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const r = i % 2 === 0 ? rOuter : rInner;
    // start at 12 o'clock, go clockwise
    const ang = (Math.PI / 2) - (i * Math.PI) / 5;
    pts.push(`${(cx + Math.cos(ang) * r).toFixed(2)},${(cy - Math.sin(ang) * r).toFixed(2)}`);
  }
  return pts.join(' ');
}

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
  compact = false,
}: {
  size?: number;
  imprintDots: WheelDot[];
  overlay?: WheelDot[];
  /** Compact preview: hide angle ticks/labels, scale dots down, use more disk. */
  compact?: boolean;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const outerR = (size / 2) - (compact ? 5 : 16); // leave room for the angle labels (full mode)
  const dotR = Math.min(7.5, Math.max(3, size * 0.024)); // scale with size so the small wheel stays clean
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Project (hue°, chroma) → (x, y). Hue 0° at right (3 o'clock), increasing
  // counter-clockwise — matching the per-pixel disk painted below.
  const project = (H: number, C: number): { x: number; y: number } => {
    const rad = (H * Math.PI) / 180;
    const r = Math.min(C / MAX_WHEEL_CHROMA, 1) * outerR;
    return { x: cx + Math.cos(rad) * r, y: cy - Math.sin(rad) * r };
  };

  // Paint the hue ring per-pixel into a canvas: every pixel at (r, θ) is
  // oklch(WHEEL_RING_L, (r/outerR)·MAX_CHROMA, θ). Continuous → no facets, and
  // the chroma genuinely fades to neutral grey at the centre (matches the
  // matplotlib reference wheel rather than faking the fade with a bg overlay).
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const px = Math.round(size * dpr);
    canvas.width = px;
    canvas.height = px;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const img = ctx.createImageData(px, px);
    const data = img.data;
    const r0 = outerR * dpr;
    const cxp = cx * dpr;
    const cyp = cy * dpr;
    for (let y = 0; y < px; y++) {
      for (let x = 0; x < px; x++) {
        const dx = x - cxp;
        const dy = y - cyp;
        const r = Math.hypot(dx, dy);
        const idx = (y * px + x) * 4;
        if (r > r0) continue; // leave fully transparent outside the disk
        let theta = (Math.atan2(-dy, dx) * 180) / Math.PI;
        if (theta < 0) theta += 360;
        const c = Math.min(r / r0, 1) * MAX_WHEEL_CHROMA;
        const [rr, gg, bb] = oklchToRgb(WHEEL_RING_L, c, theta);
        data[idx] = rr;
        data[idx + 1] = gg;
        data[idx + 2] = bb;
        data[idx + 3] = r > r0 - dpr ? Math.round(255 * (r0 - r) / dpr) : 255; // 1px AA edge
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [size, outerR, cx, cy]);

  // Chroma envelope — the band all imprint hues fall inside (low-chroma corridor).
  const cs = imprintDots.map((d) => d.C);
  const rInner = (Math.min(...cs) / MAX_WHEEL_CHROMA) * outerR;
  const rOuter = (Math.max(...cs) / MAX_WHEEL_CHROMA) * outerR;
  const rMid = (rInner + rOuter) / 2;
  const ticks = compact ? [] : [0, 90, 180, 270];

  return (
    <Box sx={{ position: 'relative', width: size, height: size }}>
      <Box
        component="canvas"
        ref={canvasRef}
        sx={{
          position: 'absolute', inset: 0,
          width: size, height: size,
          borderRadius: '50%',
          boxShadow: 'inset 0 0 0 1px var(--rule)',
        }}
      />
      <Box component="svg" viewBox={`0 0 ${size} ${size}`} sx={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
        {/* Low-chroma corridor: shaded annulus + dashed edges */}
        <circle
          cx={cx} cy={cy} r={rMid}
          fill="none"
          stroke="var(--ink)"
          strokeOpacity={0.10}
          strokeWidth={Math.max(0, rOuter - rInner)}
        />
        <circle cx={cx} cy={cy} r={rInner} fill="none" stroke="var(--ink)" strokeOpacity={0.28} strokeWidth={1} strokeDasharray="2 3" />
        <circle cx={cx} cy={cy} r={rOuter} fill="none" stroke="var(--ink)" strokeOpacity={0.28} strokeWidth={1} strokeDasharray="2 3" />

        {/* Angle ticks + labels (0° = 3 o'clock, CCW) */}
        {ticks.map((deg) => {
          const rad = (deg * Math.PI) / 180;
          const x1 = cx + Math.cos(rad) * outerR;
          const y1 = cy - Math.sin(rad) * outerR;
          const x2 = cx + Math.cos(rad) * (outerR + 5);
          const y2 = cy - Math.sin(rad) * (outerR + 5);
          const lx = cx + Math.cos(rad) * (outerR + 12);
          const ly = cy - Math.sin(rad) * (outerR + 12);
          return (
            <g key={deg}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--ink-muted)" strokeWidth={1} />
              <text x={lx} y={ly} fontSize={8} fill="var(--ink-muted)" textAnchor="middle" dominantBaseline="middle" style={{ fontFamily: 'monospace' }}>
                {deg}°
              </text>
            </g>
          );
        })}

        {/* Overlay palette (hollow rings) — below imprint dots so imprint stays dominant */}
        {overlay && overlay.map((d, i) => {
          const { x, y } = project(d.H, d.C);
          return (
            <g key={`o-${i}`}>
              <title>{d.hex}</title>
              <circle cx={x} cy={y} r={dotR - 1} fill="none" stroke="var(--bg-page)" strokeWidth={3} opacity={0.9} />
              <circle cx={x} cy={y} r={dotR - 1} fill="none" stroke={d.hex} strokeWidth={2.25} opacity={0.95} />
            </g>
          );
        })}

        {/* Imprint dots — white halo + filled dot; slot 0 (brand) drawn as a star */}
        {imprintDots.map((d, i) => {
          const { x, y } = project(d.H, d.C);
          if (i === 0) {
            return (
              <g key={i}>
                <title>{d.hex}</title>
                <polygon points={starPoints(x, y, dotR + 2.5, (dotR + 2.5) / 2.3)} fill={d.hex} stroke="var(--ink)" strokeWidth={1.5} strokeLinejoin="round" style={{ cursor: 'pointer' }} />
              </g>
            );
          }
          return (
            <g key={i}>
              <title>{d.hex}</title>
              <circle cx={x} cy={y} r={dotR + 1} fill="var(--bg-page)" />
              <circle cx={x} cy={y} r={dotR} fill={d.hex} stroke="var(--bg-page)" strokeWidth={1} style={{ cursor: 'pointer' }} />
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
    void navigator.clipboard
      .writeText(code)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      })
      .catch(() => {
        // Silently ignore — clipboard API can fail in insecure contexts.
      });
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
        type="button"
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
// ΔE distance matrix — generated by scripts/palette-matrix-export.py
// ─────────────────────────────────────────────────────────────────────────────

const MATRIX_LABELS: string[] = matrixData.labels;
const MATRIX_HEXES: string[] = matrixData.hexes;
const [DE_T_BAD, DE_T_WARN, DE_T_OK] = matrixData.thresholds; // 5 / 10 / 15 (Petroff 2021)

/** Background tint for a ΔE cell — low distance is the problem, so <5 is the
 *  loudest. Mirrors _palette_common.cell_class thresholds. */
function deltaECellBg(v: number): string {
  if (v <= 0) return 'transparent'; // diagonal
  if (v < DE_T_BAD) return 'rgba(174, 48, 48, 0.26)'; // <5 indistinguishable
  if (v < DE_T_WARN) return 'rgba(189, 130, 51, 0.22)'; // <10 weak
  if (v < DE_T_OK) return 'rgba(221, 204, 119, 0.18)'; // <15 acceptable
  return 'transparent'; // >=15 comfortable
}

const DE_LEGEND: { label: string; bg: string }[] = [
  { label: '<5 indistinct', bg: 'rgba(174, 48, 48, 0.26)' },
  { label: '<10 weak', bg: 'rgba(189, 130, 51, 0.22)' },
  { label: '<15 acceptable', bg: 'rgba(221, 204, 119, 0.18)' },
  { label: '≥15 comfortable', bg: 'transparent' },
];

function DeltaEMatrix({
  title,
  matrix,
  breakdown,
}: {
  title: string;
  matrix: number[][];
  breakdown?: { label: string; m: number[][] }[];
}) {
  const dot = (hx: string, label: string) => (
    <Box sx={{ width: 11, height: 11, borderRadius: '50%', bgcolor: hx, mx: 'auto', boxShadow: '0 0 0 1px var(--rule)' }} title={label} />
  );
  return (
    <Box sx={{ minWidth: 0 }}>
      <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink)', fontWeight: 600, mb: 1 }}>{title}</Box>
      <Box sx={{ overflowX: 'auto' }}>
        <Box component="table" sx={{ borderCollapse: 'collapse', fontFamily: typography.mono, fontSize: '9px' }}>
          <Box component="thead">
            <Box component="tr">
              <Box component="th" sx={{ width: 14 }} />
              {MATRIX_HEXES.map((hx, j) => (
                <Box component="th" key={j} sx={{ p: '2px' }}>{dot(hx, MATRIX_LABELS[j])}</Box>
              ))}
            </Box>
          </Box>
          <Box component="tbody">
            {matrix.map((row, i) => (
              <Box component="tr" key={i}>
                <Box component="th" sx={{ p: '2px' }}>{dot(MATRIX_HEXES[i], MATRIX_LABELS[i])}</Box>
                {row.map((v, j) => {
                  const tip = i === j
                    ? MATRIX_LABELS[i]
                    : breakdown
                      ? `${MATRIX_LABELS[i]} ↔ ${MATRIX_LABELS[j]} — ${breakdown.map(b => `${b.label} ${b.m[i][j].toFixed(1)}`).join(' · ')}`
                      : `${MATRIX_LABELS[i]} ↔ ${MATRIX_LABELS[j]} — ΔE ${v.toFixed(1)}`;
                  return (
                    <Box
                      component="td"
                      key={j}
                      title={tip}
                      sx={{
                        width: 21, height: 17, textAlign: 'center',
                        border: '1px solid var(--rule)',
                        bgcolor: deltaECellBg(v),
                        color: i === j ? 'var(--rule)' : v < DE_T_WARN ? 'var(--ink)' : 'var(--ink-muted)',
                        fontWeight: v > 0 && v < DE_T_BAD ? 700 : 400,
                        cursor: 'help',
                      }}
                    >
                      {i === j ? '·' : v.toFixed(0)}
                    </Box>
                  );
                })}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
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
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  /** Hero wheel: collapsed = small preview; expanded = larger + comparison toggles. */
  const [wheelOpen, setWheelOpen] = useState(false);

  const copyHex = (hex: string) => {
    void navigator.clipboard
      .writeText(hex)
      .then(() => {
        setCopiedHex(hex);
        setTimeout(() => setCopiedHex((c) => (c === hex ? null : c)), 1500);
      })
      .catch(() => {
        // Silently ignore — clipboard API can fail in insecure contexts.
      });
  };

  useEffect(() => {
    trackPageview('/palette');
  }, [trackPageview]);

  const sortedPalette: Swatch[] = useMemo(
    () => (sort === 'imprint' ? PALETTE : CVD_OPTIMAL_ORDER.map(i => PALETTE[i])),
    [sort]
  );

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
        <title>imprint palette | anyplot.ai</title>
        <meta name="description" content="imprint — anyplot's categorical palette: 8 colorblind-safe hues plus 3 semantic anchors (amber, neutral, muted), tuned for warm-paper rendering and validated against deuteranopia / protanopia / tritanopia." />
        <meta property="og:title" content="imprint palette | anyplot.ai" />
        <meta property="og:description" content="imprint — anyplot's colorblind-safe categorical palette: 8 hues plus 3 semantic anchors." />
        <link rel="canonical" href="https://anyplot.ai/palette" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* 1. HERO — short lede + a compact hue–chroma wheel. Click the wheel to
            enlarge it and reveal the palette-comparison toggles. */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>anyplot&apos;s imprint palette</em>} />
          <Box sx={{ ...proseColumnSx, mt: 3 }}>
            {/* sm+: wheel on the left, lede on the right (row-reverse keeps the
                lede first in the DOM, so on mobile it still reads text-then-wheel). */}
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row-reverse' }, gap: { xs: 2.5, sm: 4 }, alignItems: { xs: 'flex-start', sm: 'center' }, justifyContent: 'flex-end' }}>
              <Box sx={textStyle}>
                <strong>imprint</strong> is anyplot&apos;s categorical palette — 8 hues plus 3 semantic
                anchors. low-chroma and warm-tinted for cream paper, validated against deuteranopia /
                protanopia / tritanopia. built to let the data speak.
              </Box>
              {/* Compact wheel — a button that toggles the expanded comparison view */}
              <Box sx={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.75, alignSelf: { xs: 'center', sm: 'auto' } }}>
                <Box
                  component="button"
                  type="button"
                  onClick={() => setWheelOpen((o) => !o)}
                  aria-expanded={wheelOpen}
                  aria-label={wheelOpen ? 'Collapse the hue–chroma wheel' : 'Expand the hue–chroma wheel to compare palettes'}
                  sx={{
                    background: 'none', border: 'none', p: 0, m: 0,
                    cursor: 'pointer', lineHeight: 0, borderRadius: '50%',
                    transition: 'transform 0.15s',
                    '&:hover': { transform: 'scale(1.03)' },
                  }}
                >
                  <ChromaWheel
                    size={wheelOpen ? 260 : 128}
                    compact={!wheelOpen}
                    imprintDots={imprintDots}
                    overlay={wheelOpen ? overlayDots : undefined}
                  />
                </Box>
                <Box sx={{ fontFamily: typography.mono, fontSize: '10px', color: wheelOpen ? 'var(--ink-muted)' : colors.primary }}>
                  {wheelOpen ? 'click to close' : 'compare ▸'}
                </Box>
              </Box>
            </Box>

            {/* Expanded: comparison toggles + the wheel legend */}
            <Collapse in={wheelOpen}>
              <Box sx={{ mt: 2.5, borderTop: '1px solid var(--rule)', pt: 2.5 }}>
                <Box sx={{ fontSize: '13px', color: 'var(--ink-soft)', lineHeight: 1.6 }}>
                  where imprint sits in hue–chroma space — eight hues inside a narrow low-chroma band,
                  spread evenly around the wheel. overlay another published categorical palette to compare:
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1.5 }}>
                  {COMPARISONS.map((c) => {
                    const active = compareId === c.id;
                    return (
                      <Box
                        key={c.id}
                        component="button"
                        type="button"
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
                <Box sx={{ fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)', mt: 1.75, lineHeight: 1.5 }}>
                  hue counter-clockwise from 3 o&apos;clock · chroma = distance from centre · ★ = brand · shaded band = imprint&apos;s low-chroma corridor
                  {compareId && (
                    <Box component="span"> · rings = {COMPARISONS.find((c) => c.id === compareId)?.name}</Box>
                  )}
                </Box>
              </Box>
            </Collapse>
          </Box>
        </Box>

        {/* 2. PALETTE GRID + SORT TOGGLE */}
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
                    type="button"
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
              <Box sx={{ fontFamily: typography.mono, lineHeight: 1.55, mb: 2, p: 2, borderLeft: `2px solid ${colors.primary}`, backgroundColor: 'var(--bg-surface)' }}>
                <Box sx={{ fontSize: '12px', color: 'var(--ink)', fontWeight: 600, mb: 1, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  why use CVD-optimal sort?
                </Box>
                <Box sx={{ fontSize: '12px', color: 'var(--ink-soft)', mb: 1.5 }}>
                  this ordering picks each next slot by maximising ΔE under the worst of deuteranopia /
                  protanopia / tritanopia simulation against the already-placed set. it&apos;s the best choice
                  when colour alone has to carry the categorical encoding for users with red-green colour
                  vision deficiency — e.g. small-n charts in publications targeting CVD-first audiences,
                  status-only legends, or signage-style summary tiles.
                </Box>

                {/* Compact per-n table — only shown in CVD mode since that's where the trade-off matters */}
                <Box sx={{ overflowX: 'auto', mt: 2 }}>
                  <Box component="table" sx={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '11px',
                    '& th, & td': { padding: '4px 10px', textAlign: 'left', borderBottom: '1px solid var(--rule)' },
                    '& th': { color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' },
                  }}>
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
                            <td style={{ textAlign: 'right', color: 'var(--ink-muted)' }}>{de.toFixed(2)}</td>
                            <td style={{ textAlign: 'right', color: gain > 0 ? '#007A59' : 'var(--ink-muted)', fontWeight: gain > 0 ? 600 : 400 }}>
                              {altDe.toFixed(2)}{gain > 0 ? ` (+${gain.toFixed(2)})` : gain < 0 ? ` (${gain.toFixed(2)})` : ' (=)'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </Box>
                </Box>

                <Box sx={{ fontSize: '12px', color: 'var(--ink-soft)', mt: 2 }}>
                  <Box component="strong" sx={{ color: 'var(--ink)' }}>trade-off:</Box> the first 4 slots end
                  up with two greens (brand at slot 0 + lime at slot 2) and two purples (lavender at slot 1 +
                  rose at slot 3) side by side — the eye loses the &ldquo;four distinct hue families&rdquo;
                  cue that imprint default gives you. n=2..6 gains 0.71–5.83 ΔE under CVD; n=7..8 are
                  identical because both sortings ship the same 8 hexes.
                </Box>
                <Box sx={{ fontSize: '12px', color: 'var(--ink-muted)', mt: 1 }}>
                  <Box component="strong" sx={{ color: 'var(--ink)' }}>when to switch:</Box> CVD-first
                  audience + small-n (n ≤ 4) + colour is the only encoding. otherwise the imprint default is
                  the better balance — and at n = 7..8 you should add a marker shape or linestyle either way.
                </Box>
              </Box>
            )}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
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
                        display: 'flex', flexDirection: 'column',
                        background: 'none', border: 'none', padding: 0,
                        cursor: 'pointer',
                        textAlign: 'left',
                        '&:hover .v3-sw': { transform: 'scale(1.02)' },
                      }}
                    >
                      <Box
                        className="v3-sw"
                        sx={{
                          height: 92,
                          bgcolor: s.hex,
                          color: textOn(s.hex),
                          display: 'flex', flexDirection: 'column', justifyContent: 'flex-end',
                          p: 1.25,
                          fontFamily: typography.mono,
                          borderRadius: 1,
                          boxShadow: i === 0 ? `inset 0 0 0 2px var(--ink)` : 'inset 0 0 0 1px var(--rule)',
                          transition: 'transform 0.15s',
                        }}
                      >
                        <Box sx={{ fontSize: '12px', fontWeight: 600, lineHeight: 1.2 }}>{s.name}</Box>
                        <Box sx={{ fontSize: '11px', opacity: 0.85 }}>{copied ? 'copied ✓' : s.hex}</Box>
                      </Box>
                      <Box sx={{
                        fontFamily: typography.mono, fontSize: '10px',
                        mt: 1, lineHeight: 1.65, color: 'var(--ink-muted)',
                      }}>
                        <Box sx={{ color: 'var(--ink-soft)' }}>
                          <Box component="span" sx={{ color: 'var(--ink)', fontWeight: 600 }}>slot {i}{i === 0 ? ' ★' : ''}</Box>
                          {' · '}{s.role}
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                          <Box component="span">H <Box component="span" sx={{ color: 'var(--ink)' }}>{s.H.toFixed(0)}°</Box></Box>
                          <Box component="span">C <Box component="span" sx={{ color: 'var(--ink)' }}>{s.C.toFixed(2)}</Box></Box>
                        </Box>
                        <Tooltip title="min ΔE to any other slot — normal vision · worst of deuteranopia / protanopia / tritanopia">
                          <Box sx={{ mt: 0.25, cursor: 'help' }}>
                            ΔE <Box component="span" sx={{ color: 'var(--ink)' }}>{s.minNorm.toFixed(1)}</Box> norm
                            {' · '}<Box component="span" sx={{ color: 'var(--ink)' }}>{s.minCvd.toFixed(1)}</Box> cvd
                          </Box>
                        </Tooltip>
                        <Box sx={{ display: 'flex', gap: 1.5, mt: 0.25 }}>
                          <Tooltip title="WCAG contrast on cream bg #FAF8F1 — graphical objects 3:1 minimum">
                            <Box component="span" sx={{ color: s.wcagL >= 3 ? '#007A59' : '#b62d2d', cursor: 'help' }}>
                              ☼ {s.wcagL.toFixed(1)}:1
                            </Box>
                          </Tooltip>
                          <Tooltip title="WCAG contrast on dark bg #121210">
                            <Box component="span" sx={{ color: s.wcagD >= 3 ? '#007A59' : '#b62d2d', cursor: 'help' }}>
                              ☽ {s.wcagD.toFixed(1)}:1
                            </Box>
                          </Tooltip>
                        </Box>
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
              for continuous data the categorical pool is replaced with two palette-derived colormaps.
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
                  background: 'linear-gradient(to right, #AE3030, var(--bg-surface), #4467A3)',
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
              the diverging midpoint flips per theme — <code>#FAF8F1</code> on cream bg / <code>#1A1A17</code>
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

        {/* 5. WCAG AUDIT (collapsible) — was section 6 before "best variant for CVD users" was folded into the sort toggle expanded view */}
        <Box component="section" sx={sectionSx}>
          <Box sx={proseColumnSx}>
            <CollapsibleSection title="WCAG contrast on both themes (and the outline pattern)">
              <Box sx={textStyle}>
                muted palettes share a known limit: the lighter members carry their distinguishability through
                chroma, not L-spread. On cream bg <code>#FAF8F1</code>, five categorical hues + amber fall under
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

              {/* Pairwise colour-distance (ΔE) matrices — generated by
                  scripts/palette-matrix-export.py from the same CAM02-UCS +
                  Machado-2009 CVD math used across the project. */}
              <Box sx={{ mt: 4 }}>
                <Box sx={{ fontFamily: typography.mono, fontSize: '12px', fontWeight: 600, color: 'var(--ink)', mb: 1 }}>
                  pairwise colour distance (ΔE)
                </Box>
                <Box sx={{ ...textStyle, fontSize: '13px' }}>
                  the numbers behind each hue&apos;s <code>norm</code> / <code>cvd</code> readout, in full — pairwise
                  ΔE in CAM02-UCS for the 8 hues plus the amber and neutral anchors. lower = closer = harder to
                  tell apart. the worst-CVD grid takes the lowest of the deuteranopia / protanopia / tritanopia
                  simulations per pair; hover any cell for the breakdown.
                </Box>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3, mt: 2 }}>
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
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, mt: 2, fontFamily: typography.mono, fontSize: '10px', color: 'var(--ink-muted)', alignItems: 'center' }}>
                  {DE_LEGEND.map((l) => (
                    <Box key={l.label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Box sx={{ width: 12, height: 12, bgcolor: l.bg, border: '1px solid var(--rule)' }} />
                      {l.label}
                    </Box>
                  ))}
                  <Box component="span" sx={{ ml: 'auto' }}>thresholds: Petroff 2021 · amber + neutral (light-theme ink) sit outside the categorical pool</Box>
                </Box>
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>

        {/* 6. HISTORY (collapsible) */}
        <Box component="section" sx={sectionSx}>
          <Box sx={proseColumnSx}>
            <CollapsibleSection title="palette history — how we got here">
              <Box sx={{ fontSize: '13px', color: 'var(--ink-soft)', lineHeight: 1.6, mb: 2.5 }}>
                four versions, each fixing a concrete failure of the last. the interactive hue–chroma
                wheel at the top of the page overlays any of these against imprint.
              </Box>
              <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', mb: 1.5 }}>
                version timeline
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {HISTORY.map((entry) => (
                  <Box key={entry.id}>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mb: 1, flexWrap: 'wrap' }}>
                      <Box sx={{ fontFamily: typography.mono, fontSize: '13px', color: 'var(--ink)', fontWeight: 600 }}>
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

              {/* Credit / inspiration + method references */}
              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid var(--rule)', fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)', lineHeight: 1.7 }}>
                the candidate-palette search drew on Anselm Hahn&apos;s{' '}
                <Box
                  component="a"
                  href="https://github.com/Anselmoo/dracula-palette"
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ color: 'var(--ink-soft)', textDecoration: 'underline', textDecorationColor: 'var(--rule)', '&:hover': { color: colors.primary, textDecorationColor: colors.primary } }}
                >
                  dracula-palette
                </Box>{' '}
                colour-harmony generator. perceptual distances in CAM02-UCS (Petroff 2021); CVD via Machado et al. 2009.
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>
      </Box>
    </>
  );
}
