import matrixData from 'src/data/paletteMatrices.json';

export const [DE_T_BAD, DE_T_WARN, DE_T_OK] = matrixData.thresholds; // 5 / 10 / 15 (Petroff 2021)

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
