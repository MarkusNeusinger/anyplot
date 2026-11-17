import { describe, expect, it } from 'vitest';

import { monoWidth } from 'src/sections/about/monoWidth';

describe('monoWidth', () => {
  // Measured in Chromium: the full binary lays "brand green" out at 84.48px (0.64em a character),
  // the headless shell, which rounds each advance to a whole pixel, at 88px.
  it('counts a 12px character at 8px, the whole-pixel advance, which is wider', () => {
    expect(monoWidth('brand green', 12)).toBe(88);
    expect(monoWidth('julia & javascript · 15 libraries', 12)).toBe(264);
  });

  // At 11px the rounded advance is 7px, narrower than the fractional 7.04px, so that one counts.
  it('counts an 11px character at its fractional advance, which is wider', () => {
    expect(monoWidth('2026-11-03 · 4.0.0', 11)).toBe(127);
  });

  it('is never narrower than either rendering, at the sizes the figures use', () => {
    for (const size of [11, 12, 13, 14]) {
      for (const text of ['today', 'first github release', '(up to 4 times)', 'mastery']) {
        expect(monoWidth(text, size)).toBeGreaterThanOrEqual(text.length * size * 0.64);
        expect(monoWidth(text, size)).toBeGreaterThanOrEqual(text.length * Math.round(size * 0.64));
      }
    }
  });
});
