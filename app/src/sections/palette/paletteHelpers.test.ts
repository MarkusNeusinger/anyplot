import { describe, expect, it } from 'vitest';

import {
  COMPARISONS,
  DE_T_BAD,
  DE_T_OK,
  DE_T_WARN,
  deltaECellBg,
  oklchToRgb,
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

  describe('textOn', () => {
    it('returns dark ink (#1A1A17) on light swatches and light ink (#F0EFE8) on dark swatches', () => {
      expect(textOn('#FFFFFF')).toBe('#1A1A17');
      expect(textOn('#F5F3EC')).toBe('#1A1A17');
      expect(textOn('#DDCC77')).toBe('#1A1A17');
      expect(textOn('#000000')).toBe('#F0EFE8');
      expect(textOn('#1A1A17')).toBe('#F0EFE8');
      expect(textOn('#4467A3')).toBe('#F0EFE8');
      expect(textOn('009E73')).toBe('#F0EFE8');
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
