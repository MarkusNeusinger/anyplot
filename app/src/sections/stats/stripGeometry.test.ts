import { describe, expect, it } from 'vitest';

import { CHART_PX, columnPx, MIN_BAR_PX, STRIP_BAR } from 'src/sections/stats/stripGeometry';
import { colors } from 'src/theme';

describe('columnPx', () => {
  it('draws a day without anything at the floor', () => {
    expect(columnPx(0, 300)).toBe(MIN_BAR_PX);
    expect(columnPx(0, 0)).toBe(MIN_BAR_PX);
  });

  it('never draws a day with something below a day without', () => {
    // At a peak of 300, one read is 0.23 px: the floor holds it, it is never shorter than an empty day.
    expect(columnPx(1, 300)).toBe(MIN_BAR_PX);
    expect(columnPx(1, 300)).toBeGreaterThanOrEqual(columnPx(0, 300));
  });

  it('fills the strip on the busiest day and scales the rest by their number', () => {
    expect(columnPx(300, 300)).toBe(CHART_PX);
    expect(columnPx(150, 300)).toBe(CHART_PX / 2);
  });

  it('rises with the number and never falls', () => {
    const heights = Array.from({ length: 301 }, (_, total) => columnPx(total, 300));
    for (let total = 1; total < heights.length; total += 1) {
      expect(heights[total]).toBeGreaterThanOrEqual(heights[total - 1]);
    }
  });
});

describe('STRIP_BAR', () => {
  it('is the darker brand green, quiet at rest and stronger under the pointer', () => {
    expect(STRIP_BAR.color).toBe(colors.primaryDark);
    expect(STRIP_BAR.opacity).toBeLessThan(STRIP_BAR.activeOpacity);
    expect(STRIP_BAR.activeOpacity).toBeLessThanOrEqual(1);
  });
});
