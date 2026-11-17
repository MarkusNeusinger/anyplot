import { describe, expect, it } from 'vitest';

import { PALETTE } from 'src/pages/PalettePage.helpers';
import {
  COMPARISONS,
  contrastRatio,
  DE_T_BAD,
  DE_T_OK,
  DE_T_WARN,
  deltaECellBg,
  INK_DARK,
  INK_LIGHT,
  oklchToRgb,
  relativeLuminance,
  starPoints,
  textOn,
} from 'src/sections/palette/paletteHelpers';

describe('paletteHelpers', () => {
  describe('thresholds and comparison palettes', () => {
    it('exports the Petroff 2021 ΔE thresholds in ascending order', () => {
      expect([DE_T_BAD, DE_T_WARN, DE_T_OK]).toEqual([5, 10, 15]);
    });

    it('exports the four comparison palettes with valid hex and OKLCH entries', () => {
      expect(COMPARISONS.map(c => c.id)).toEqual(['okabe', 'tol', 'set2', 'prev']);
      for (const comp of COMPARISONS) {
        expect(comp.name.length).toBeGreaterThan(0);
        expect(comp.hexes.length).toBeGreaterThanOrEqual(7);
        for (const swatch of comp.hexes) {
          expect(swatch.hex).toMatch(/^#[0-9A-F]{6}$/);
          expect(swatch.L).toBeGreaterThan(0);
          expect(swatch.L).toBeLessThanOrEqual(1);
          expect(swatch.C).toBeGreaterThanOrEqual(0);
          expect(swatch.H).toBeGreaterThanOrEqual(0);
          expect(swatch.H).toBeLessThan(360);
        }
      }
    });
  });

  describe('oklchToRgb', () => {
    it('maps black (L=0, C=0) and white (L=1, C=0) to the sRGB endpoints', () => {
      expect(oklchToRgb(0, 0, 0)).toEqual([0, 0, 0]);
      expect(oklchToRgb(1, 0, 0)).toEqual([255, 255, 255]);
    });

    it('produces neutral grey with equal R, G, B channels when chroma is zero', () => {
      const [r, g, b] = oklchToRgb(0.5, 0, 180);
      expect(r).toBe(g);
      expect(g).toBe(b);
      expect(r).toBeGreaterThan(0);
      expect(r).toBeLessThan(255);
    });

    it('approximates the brand-green sRGB triplet (#009E73) at its OKLCH coordinates', () => {
      const [r, g, b] = oklchToRgb(0.62, 0.13, 165.5);
      expect(r).toBeLessThanOrEqual(2);
      expect(g).toBeGreaterThanOrEqual(156);
      expect(g).toBeLessThanOrEqual(160);
      expect(b).toBeGreaterThanOrEqual(113);
      expect(b).toBeLessThanOrEqual(117);
    });

    it('clamps out-of-gamut high-chroma coordinates into 0..255 integers', () => {
      const rgb = oklchToRgb(0.85, 0.4, 30);
      for (const ch of rgb) {
        expect(Number.isInteger(ch)).toBe(true);
        expect(ch).toBeGreaterThanOrEqual(0);
        expect(ch).toBeLessThanOrEqual(255);
      }
    });

    it('is periodic modulo 360 degrees in hue', () => {
      expect(oklchToRgb(0.72, 0.14, 0)).toEqual(oklchToRgb(0.72, 0.14, 360));
    });
  });

  describe('starPoints', () => {
    it('builds a 10-vertex alternating star starting at 12 o’clock', () => {
      const points = starPoints(100, 100, 10, 5).split(' ');
      expect(points).toHaveLength(10);
      // Vertex 0: 12 o'clock outer tip (cx, cy - rOuter)
      expect(points[0]).toBe('100.00,90.00');
      // Vertex 5: 6 o'clock inner valley (cx, cy + rInner)
      expect(points[5]).toBe('100.00,105.00');
    });
  });

  describe('contrastRatio', () => {
    it('follows the WCAG formula: 21 for black on white, 1 for a colour on itself, symmetric', () => {
      expect(contrastRatio('#000000', '#FFFFFF')).toBeCloseTo(21, 5);
      expect(contrastRatio('#4467A3', '#4467A3')).toBeCloseTo(1, 5);
      expect(contrastRatio('#2ABCCD', INK_DARK)).toBeCloseTo(
        contrastRatio(INK_DARK, '#2ABCCD'),
        10
      );
      expect(relativeLuminance('#FFFFFF')).toBeCloseTo(1, 5);
      expect(relativeLuminance('000000')).toBe(0);
    });
  });

  describe('textOn', () => {
    it('returns dark ink on light swatches and light ink on dark swatches', () => {
      expect(textOn('#FFFFFF')).toBe(INK_DARK);
      expect(textOn('#F5F3EC')).toBe(INK_DARK);
      expect(textOn('#000000')).toBe(INK_LIGHT);
      expect(textOn('#1A1A17')).toBe(INK_LIGHT);
    });

    // The swatch labels of /palette: the eight imprint hues and the semantic anchors.
    it.each([
      ['brand green', '009E73', INK_DARK],
      ['lavender', '#C475FD', INK_DARK],
      ['blue', '#4467A3', INK_LIGHT],
      ['ochre', '#BD8233', INK_DARK],
      ['matte red', '#AE3030', INK_LIGHT],
      ['cyan', '#2ABCCD', INK_DARK],
      ['rose', '#954477', INK_LIGHT],
      ['lime', '#99B314', INK_DARK],
      ['amber', '#DDCC77', INK_DARK],
      ['neutral, light theme', '#1A1A17', INK_LIGHT],
      ['neutral, dark theme', '#F0EFE8', INK_DARK],
      ['muted, light theme', '#6B6A63', INK_LIGHT],
      ['muted, dark theme', '#A8A79F', INK_DARK],
    ])('labels %s (%s) in the ink with the higher contrast', (_, hex, ink) => {
      expect(textOn(hex)).toBe(ink);
      const other = ink === INK_DARK ? INK_LIGHT : INK_DARK;
      expect(contrastRatio(ink, hex)).toBeGreaterThan(contrastRatio(other, hex));
    });

    it('gives every imprint hue a label of at least 4.5:1 (WCAG AA for small text)', () => {
      for (const { hex, name } of PALETTE) {
        expect(contrastRatio(textOn(hex), hex), name).toBeGreaterThanOrEqual(4.5);
      }
    });
  });

  describe('deltaECellBg', () => {
    it('returns transparent on the diagonal and for comfortable distances (>= 15)', () => {
      expect(deltaECellBg(0)).toBe('transparent');
      expect(deltaECellBg(-1)).toBe('transparent');
      expect(deltaECellBg(DE_T_OK)).toBe('transparent');
      expect(deltaECellBg(25)).toBe('transparent');
    });

    it('returns the red, amber, and yellow tints across the three warning bands', () => {
      expect(deltaECellBg(0.1)).toBe('rgba(174, 48, 48, 0.26)');
      expect(deltaECellBg(DE_T_BAD - 0.01)).toBe('rgba(174, 48, 48, 0.26)');
      expect(deltaECellBg(DE_T_BAD)).toBe('rgba(189, 130, 51, 0.22)');
      expect(deltaECellBg(DE_T_WARN - 0.01)).toBe('rgba(189, 130, 51, 0.22)');
      expect(deltaECellBg(DE_T_WARN)).toBe('rgba(221, 204, 119, 0.18)');
      expect(deltaECellBg(DE_T_OK - 0.01)).toBe('rgba(221, 204, 119, 0.18)');
    });
  });
});
