import matrixData from 'src/data/paletteMatrices.json';
import type { CompPalette } from 'src/sections/palette/types';

export const [DE_T_BAD, DE_T_WARN, DE_T_OK] = matrixData.thresholds; // 5 / 10 / 15 (Petroff 2021)

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

export const COMPARISONS: CompPalette[] = [OKABE_ITO, TOL_MUTED, SET2, ANYPLOT_PREV];

/** OKLCH (L 0..1, C, H°) → sRGB [r,g,b] 0..255, clamped to gamut.
 *  Björn Ottosson's OKLab→linear-sRGB matrices. Used to paint the wheel disk
 *  per-pixel so the hue ring is seamless (no conic-gradient facets). */
export function oklchToRgb(L: number, C: number, H: number): [number, number, number] {
  const h = (H * Math.PI) / 180;
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.291485548 * b;
  const l = l_ * l_ * l_;
  const m = m_ * m_ * m_;
  const s = s_ * s_ * s_;
  const lin = (c: number) => {
    const v = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
    return Math.max(0, Math.min(1, v));
  };
  const r = lin(+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
  const g = lin(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
  const bb = lin(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s);
  return [Math.round(r * 255), Math.round(g * 255), Math.round(bb * 255)];
}

/** 5-point star polygon points string, centred at (cx,cy). */
export function starPoints(cx: number, cy: number, rOuter: number, rInner: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const r = i % 2 === 0 ? rOuter : rInner;
    // start at 12 o'clock, go clockwise
    const ang = Math.PI / 2 - (i * Math.PI) / 5;
    pts.push(`${(cx + Math.cos(ang) * r).toFixed(2)},${(cy - Math.sin(ang) * r).toFixed(2)}`);
  }
  return pts.join(' ');
}

/** Pick a readable text color (ink-dark or ink-light) for a hex bg via WCAG luminance. */
export function textOn(hex: string): string {
  const s = hex.replace('#', '');
  const r = parseInt(s.slice(0, 2), 16) / 255;
  const g = parseInt(s.slice(2, 4), 16) / 255;
  const b = parseInt(s.slice(4, 6), 16) / 255;
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  return L > 0.5 ? '#1A1A17' : '#F0EFE8';
}

/** Background tint for a ΔE cell — low distance is the problem, so <5 is the
 *  loudest. Mirrors _palette_common.cell_class thresholds. */
export function deltaECellBg(v: number): string {
  if (v <= 0) return 'transparent'; // diagonal
  if (v < DE_T_BAD) return 'rgba(174, 48, 48, 0.26)'; // <5 indistinguishable
  if (v < DE_T_WARN) return 'rgba(189, 130, 51, 0.22)'; // <10 weak
  if (v < DE_T_OK) return 'rgba(221, 204, 119, 0.18)'; // <15 acceptable
  return 'transparent'; // >=15 comfortable
}

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

// ─────────────────────────────────────────────────────────────────────────────
// Layout
// ─────────────────────────────────────────────────────────────────────────────

export const sectionSx = { py: { xs: 2, md: 3 } };
export const proseColumnSx = { maxWidth: 880, mx: 'auto' };
