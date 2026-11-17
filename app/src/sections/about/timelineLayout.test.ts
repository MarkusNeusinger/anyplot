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

/** What is wrong with the drawn labels on `day` at an axis of `width` px; empty when nothing is. */
function problems(day: Date, width: number): string[] {
  const when = day.toISOString().slice(0, 10);
  const placed = spans(layoutTimeline(ORIGIN_EVENTS, day), width);
  const found: string[] = [];
  for (const p of placed) {
    if (p.a < 0 || p.b > width) found.push(`${when} ${width}px: ${p.what} leaves the axis`);
    if (p.level > MAX_LEVEL) found.push(`${when} ${width}px: ${p.what} above row ${MAX_LEVEL}`);
  }
  for (const [i, p] of placed.entries()) {
    for (const q of placed.slice(i + 1)) {
      if (p.side === q.side && p.level === q.level && !(p.b <= q.a || q.b <= p.a)) {
        found.push(`${when} ${width}px: ${p.what} overlaps ${q.what}`);
      }
      // A leader runs from the axis to its label, past the nearer rows of its side.
      for (const [near, far] of [
        [p, q],
        [q, p],
      ]) {
        if (
          near.side === far.side &&
          near.level < far.level &&
          far.x >= near.a &&
          far.x <= near.b
        ) {
          found.push(`${when} ${width}px: ${far.what}'s leader crosses ${near.what}`);
        }
      }
    }
  }
  return found;
}

describe('layoutTimeline', () => {
  // "today" moves every day and squeezes the spring of 2026 together, and a day whose search runs
  // out falls back to labels that may overlap. So every day for four years, at the narrowest axis
  // the page draws and at the prose column's full 760px.
  it('keeps every label on the axis and clear of the others, every day to 2030-11-17', () => {
    const found: string[] = [];
    const last = Date.UTC(2030, 10, 17, 12);
    for (let t = Date.UTC(2026, 10, 17, 12); t <= last; t += 86_400_000) {
      for (const width of [TIMELINE_MIN_WIDTH, 760]) found.push(...problems(new Date(t), width));
    }
    expect(found).toEqual([]);
  });

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
      '2026-11-03 · 4.0.0',
    ]);
  });
});
