import { describe, expect, it } from 'vitest';

import {
  CHART_PX,
  columnPx,
  MIN_BAR_PX,
  readMachineReaders,
  segmentGapPx,
} from 'src/sections/stats/machineReaders';

describe('columnPx', () => {
  it('draws a day without reads at the floor', () => {
    expect(columnPx(0, 300)).toBe(MIN_BAR_PX);
    expect(columnPx(0, 0)).toBe(MIN_BAR_PX);
  });

  it('never draws a day with reads below a day without them', () => {
    // At a peak of 300, one read is 0.23 px: the floor holds it, it is never shorter than an empty day.
    expect(columnPx(1, 300)).toBe(MIN_BAR_PX);
    expect(columnPx(1, 300)).toBeGreaterThanOrEqual(columnPx(0, 300));
  });

  it('fills the strip on the busiest day and scales the rest by their total', () => {
    expect(columnPx(300, 300)).toBe(CHART_PX);
    expect(columnPx(150, 300)).toBe(CHART_PX / 2);
  });

  it('rises with the total and never falls', () => {
    const heights = Array.from({ length: 301 }, (_, total) => columnPx(total, 300));
    for (let total = 1; total < heights.length; total += 1) {
      expect(heights[total]).toBeGreaterThanOrEqual(heights[total - 1]);
    }
  });
});

describe('segmentGapPx', () => {
  it('separates the segments of a tall column by 2 px and leaves a short or single one alone', () => {
    expect(segmentGapPx(70, 3)).toBe(2);
    expect(segmentGapPx(16, 3)).toBe(2);
    expect(segmentGapPx(15, 3)).toBe(0);
    expect(segmentGapPx(70, 1)).toBe(0);
    expect(segmentGapPx(MIN_BAR_PX, 0)).toBe(0);
  });
});

describe('readMachineReaders', () => {
  it('reads an ok answer and floors bad counts to zero', () => {
    const answer = readMachineReaders({
      status: 'ok',
      days: 28,
      points: [
        { date: '2026-11-09', for_person: 2, index_training: -1, search: '3', mcp: 4.7 },
        { nodate: true },
      ],
      totals: { for_person: 2, unverified: 26 },
      generated_at: '2026-11-09T13:50:00Z',
    });
    expect(answer?.points).toEqual([
      { date: '2026-11-09', for_person: 2, index_training: 0, search: 0, mcp: 4 },
    ]);
    expect(answer?.totals).toEqual({
      for_person: 2,
      index_training: 0,
      search: 0,
      mcp: 0,
      unverified: 26,
    });
  });

  it('refuses anything but an ok answer with days', () => {
    expect(readMachineReaders(null)).toBeNull();
    expect(readMachineReaders({ status: 'unavailable', points: [] })).toBeNull();
    expect(readMachineReaders({ status: 'ok', points: [] })).toBeNull();
    expect(readMachineReaders({ status: 'ok', points: 'nope' })).toBeNull();
  });
});
