import { describe, expect, it } from 'vitest';

import { ORIGIN_EVENTS, originDateLabel } from 'src/sections/about/figureData';
import {
  labelWidth,
  layoutTimeline,
  MAX_LEVEL,
  TIMELINE_MIN_WIDTH,
  type TimelinePoint,
} from 'src/sections/about/timelineLayout';

/** Each label's span on an axis of `width` px, as the page draws it. */
function spans(points: TimelinePoint[], width: number) {
  return points.map(point => {
    const x = (point.percent / 100) * width;
    const w = labelWidth(point.date, point.what);
    const [a, b] = point.align === 'start' ? [x, x + w] : [x - w, x];
    return { ...point, x, a, b };
  });
}

// "today" moves every day and squeezes the spring of 2026 together; the layout must hold for
// years, at the narrowest axis the page draws and at the prose column's full 760px.
const DAYS = ['2026-11-17', '2027-03-10', '2027-06-01', '2027-11-17', '2028-11-17', '2030-11-17'];

describe('layoutTimeline', () => {
  it.each(DAYS.flatMap(day => [TIMELINE_MIN_WIDTH, 760].map(width => [day, width] as const)))(
    'keeps every label on the axis and clear of the others on %s at %ipx',
    (day, width) => {
      const placed = spans(layoutTimeline(ORIGIN_EVENTS, new Date(`${day}T12:00:00Z`)), width);
      for (const p of placed) {
        expect(p.a).toBeGreaterThanOrEqual(0);
        expect(p.b).toBeLessThanOrEqual(width);
        expect(p.level).toBeLessThanOrEqual(MAX_LEVEL);
      }
      for (const [i, p] of placed.entries()) {
        for (const q of placed.slice(i + 1)) {
          if (p.side === q.side && p.level === q.level) {
            expect(p.b <= q.a || q.b <= p.a, `${p.what} and ${q.what} on ${day}`).toBe(true);
          }
          // A leader runs from the axis to its label, past the nearer rows of its side.
          for (const [near, far] of [
            [p, q],
            [q, p],
          ]) {
            if (near.side === far.side && near.level < far.level) {
              expect(
                far.x < near.a || far.x > near.b,
                `${far.what}'s leader crosses ${near.what} on ${day}`
              ).toBe(true);
            }
          }
        }
      }
    }
  );

  it('runs from the first point at 0 to today at 100, in date order', () => {
    const points = layoutTimeline(ORIGIN_EVENTS, new Date('2026-11-17T12:00:00Z'));
    expect(points.map(p => p.what)).toEqual([...ORIGIN_EVENTS.map(e => e.what), 'today']);
    expect(points[0].percent).toBe(0);
    expect(points[points.length - 1].percent).toBe(100);
    const percents = points.map(p => p.percent);
    expect([...percents].sort((a, b) => a - b)).toEqual(percents);
    expect(points[points.length - 1].today).toBe(true);
    expect(points[points.length - 1].date).toBe('');
  });

  it('writes a month as "nov 2025" and a day with its release', () => {
    expect(ORIGIN_EVENTS.map(originDateLabel)).toEqual([
      'nov 2025',
      '2026-04-07 · 1.0.0',
      '2026-04-23 · 2.0.0',
      '2026-05-18 · 2.4.0',
      '2026-06-10 · 3.0.0',
      '2026-11-02',
    ]);
  });
});
