import type { Lang } from 'src/pages/PalettePage.helpers';

export type WheelDot = { hex: string; L: number; C: number; H: number; name?: string };
export const MAX_WHEEL_CHROMA = 0.28;
export const WHEEL_RING_L = 0.72;

export const DE_LEGEND: { label: string; bg: string }[] = [
  { label: '<5 indistinct', bg: 'rgba(174, 48, 48, 0.26)' },
  { label: '<10 weak', bg: 'rgba(189, 130, 51, 0.22)' },
  { label: '<15 acceptable', bg: 'rgba(221, 204, 119, 0.18)' },
  { label: '≥15 comfortable', bg: 'transparent' },
];

export const CVD_OPTIMAL_ORDER: number[] = [0, 1, 7, 6, 4, 5, 2, 3];

export type CompPalette = {
  id: string;
  name: string;
  href?: string;
  hexes: { hex: string; L: number; C: number; H: number }[];
};

export const OKABE_ITO: CompPalette = {
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

export const TOL_MUTED: CompPalette = {
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

export const SET2: CompPalette = {
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

export const ANYPLOT_PREV: CompPalette = {
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

export const COMPARISONS: CompPalette[] = [OKABE_ITO, TOL_MUTED, SET2, ANYPLOT_PREV];

export type Anchor = {
  key: string;
  hexLight: string;
  hexDark?: string;
  role: string;
  hint: string;
};

export const ANCHORS: Anchor[] = [
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

export const HYBRID_V3_CVD: number[] = [36.19, 16.34, 13.98, 13.98, 13.7, 10.7, 8.81];
export const PURE_CVD_GREEDY: number[] = [36.19, 21.45, 19.81, 15.2, 13.7, 10.7, 8.81];

export const WCAG_TABLE: { hex: string; name: string; light: number; dark: number }[] = [
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

export type HistoryEntry = {
  id: string;
  title: string;
  hexes: string[];
  summary: string;
  href?: string;
  hrefLabel?: string;
};

export const HISTORY: HistoryEntry[] = [
  {
    id: 'v3',
    title: 'v3 — imprint (current)',
    hexes: ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD', '#954477', '#99B314'],
    summary:
      "the shipping palette — v1's hues pulled into an even tighter, lower-chroma band so the set reads editorial rather than dashboard and nothing washes out on cream. all six primary hue families are present — red / yellow / green / cyan / blue / purple — which is also why the palette doubles as the site's code-syntax coloring — every token export type gets its own colourblind-safe hue. the first four slots span four distinct hue families, and semantic red is deferred to slot 4 so it stays a free named anchor for bad / loss / error instead of landing in every 3-series chart. plus 3 anchors outside the pool: amber, neutral, muted.",
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

export const LANG_LABELS: Record<Lang, string> = {
  python: 'Python',
  r: 'R',
  julia: 'Julia',
  js: 'JavaScript',
};

// ─────────────────────────────────────────────────────────────────────────────
// Inline sub-components
// ─────────────────────────────────────────────────────────────────────────────

// Theme-adaptive tooltip. MUI's default tooltip is a fixed dark grey that
// ignores the page's light/dark mode, so paint it from the design tokens —
// they cascade from :root / [data-theme="dark"] on <html> into the portal.

export const tooltipSlotProps = {
  tooltip: {
    sx: {
      bgcolor: 'var(--bg-elevated)',
      color: 'var(--ink)',
      border: '1px solid var(--rule)',
      boxShadow: '0 6px 24px rgba(0, 0, 0, 0.18)',
      maxWidth: 320,
    },
  },
};

export function textOn(bgHex: string): string {
  const r = parseInt(bgHex.slice(1, 3), 16) / 255;
  const g = parseInt(bgHex.slice(3, 5), 16) / 255;
  const b = parseInt(bgHex.slice(5, 7), 16) / 255;
  const lin = (c: number) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return L > 0.5 ? '#1A1A17' : '#F0EFE8';
}
