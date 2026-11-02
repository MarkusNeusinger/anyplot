import { describe, expect, it } from 'vitest';

import { LIBRARIES } from 'src/constants';
import {
  countImpls,
  formatDateShort,
  formatNum,
  pingColor,
  scoreColor,
} from 'src/sections/debug/debugFormat';
import type { SpecStatus } from 'src/sections/debug/SpecMatrix';
import { colors } from 'src/theme';

function makeSpec(overrides: Partial<SpecStatus> = {}): SpecStatus {
  return {
    id: 'scatter-basic',
    title: 'Basic Scatter',
    updated: '2026-01-15T12:00:00',
    avg_score: null,
    altair: null,
    bokeh: null,
    chartjs: null,
    d3: null,
    echarts: null,
    ggplot2: null,
    highcharts: null,
    letsplot: null,
    makie: null,
    matplotlib: null,
    muix: null,
    plotly: null,
    plotnine: null,
    pygal: null,
    seaborn: null,
    ...overrides,
  };
}

describe('debugFormat', () => {
  describe('countImpls', () => {
    it('counts non-null library scores across all libraries', () => {
      expect(countImpls(makeSpec())).toBe(0);
      expect(countImpls(makeSpec({ matplotlib: 95, seaborn: 91, d3: 88 }))).toBe(3);

      const fullOverrides = Object.fromEntries(
        LIBRARIES.map(lib => [lib, 92])
      ) as Partial<SpecStatus>;
      expect(countImpls(makeSpec(fullOverrides))).toBe(LIBRARIES.length);
    });
  });

  describe('scoreColor', () => {
    it('returns muted ink for null and threshold colors for scores', () => {
      expect(scoreColor(null)).toBe('var(--ink-muted)');
      expect(scoreColor(90)).toBe(colors.success);
      expect(scoreColor(96.5)).toBe(colors.success);
      expect(scoreColor(89.9)).toBe(colors.warning);
      expect(scoreColor(75)).toBe(colors.warning);
      expect(scoreColor(74.9)).toBe(colors.error);
      expect(scoreColor(50)).toBe(colors.error);
    });
  });

  describe('formatNum', () => {
    it('formats millions, thousands, and smaller numbers', () => {
      expect(formatNum(1_000_000)).toBe('1.0M');
      expect(formatNum(2_450_000)).toBe('2.5M');
      expect(formatNum(1_000)).toBe('1.0K');
      expect(formatNum(15_640)).toBe('15.6K');
      expect(formatNum(999)).toBe((999).toLocaleString());
      expect(formatNum(0)).toBe('0');
    });
  });

  describe('formatDateShort', () => {
    it('formats valid ISO dates as short US month and day and returns invalid strings unchanged', () => {
      expect(formatDateShort('2026-01-15T12:00:00')).toBe('Jan 15');
      expect(formatDateShort('not-a-date')).toBe('not-a-date');
    });
  });

  describe('pingColor', () => {
    it('maps response latency to success, warning, and error thresholds', () => {
      expect(pingColor(0)).toBe(colors.success);
      expect(pingColor(42)).toBe(colors.success);
      expect(pingColor(74.9)).toBe(colors.success);
      expect(pingColor(75)).toBe(colors.warning);
      expect(pingColor(199.9)).toBe(colors.warning);
      expect(pingColor(200)).toBe(colors.error);
      expect(pingColor(500)).toBe(colors.error);
    });
  });
});
