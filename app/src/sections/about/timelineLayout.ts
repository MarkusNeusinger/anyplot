import { originDateLabel, type OriginEvent } from 'src/sections/about/figureData';
import { monoWidth } from 'src/sections/about/monoWidth';

/**
 * The narrowest width the drawn timeline takes. Labels are placed for this width and the points
 * drawn in percent of the axis, so on a wider axis every gap between two labels only grows and no
 * label that fits here leaves the axis there.
 */
export const TIMELINE_MIN_WIDTH = 720;

export const DATE_SIZE = 11;
export const WHAT_SIZE = 12;
const LABEL_GAP = 12;
const LEADER_CLEARANCE = 4;
export const MAX_LEVEL = 3;

export interface TimelinePoint {
  key: string;
  /** The date line ("2026-04-07 · 1.0.0"); empty for today. */
  date: string;
  /** The machine-readable date of the date line. */
  dateTime?: string;
  what: string;
  today: boolean;
  /** Position on the axis, 0 at the first point and 100 at today. */
  percent: number;
  side: 'up' | 'down';
  /** 1 is the row nearest the axis. */
  level: number;
  /** "start": the label runs right from its point; "end": it ends at its point. */
  align: 'start' | 'end';
}

const dayOf = (when: string) => {
  const [year, month, day = 1] = when.split('-').map(Number);
  return Date.UTC(year, month - 1, day);
};

/**
 * The room a label takes: its wider line, as wide as a browser draws it with fractional advances
 * or with advances rounded to whole pixels. The labels are placed from this width, not measured,
 * so the layout is the same for every visitor and the tests can check it for any day.
 */
export function labelWidth(date: string, what: string): number {
  return Math.max(monoWidth(date, DATE_SIZE), monoWidth(what, WHAT_SIZE));
}

/**
 * Places the origin's points to scale between the first one and `now`, with their labels in rows
 * above and below the axis: alternating sides as the points come, in the row nearest the axis on
 * either side where the label fits, ending at its point or starting there. A label never overlaps
 * another in its row, never leaves the axis, and a leader to a farther row never crosses a label
 * in a nearer one. A point whose label fits nowhere sends the search back to move an earlier one
 * (a few thousand tries at most, as "today" squeezes the early points together). Should none of
 * that work, the labels alternate sides in rows by their order, which may overlap; the tests check
 * that this does not happen for years to come.
 */
export function layoutTimeline(
  events: readonly OriginEvent[],
  now: Date,
  width: number = TIMELINE_MIN_WIDTH
): TimelinePoint[] {
  const points = [
    ...events.map(event => ({
      key: event.when,
      date: originDateLabel(event),
      dateTime: event.when,
      what: event.what,
      today: false,
      t: dayOf(event.when),
    })),
    {
      key: 'today',
      date: '',
      dateTime: undefined,
      what: 'today',
      today: true,
      t: Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
    },
  ];
  const start = points[0].t;
  const span = Math.max(points[points.length - 1].t - start, 1);
  const located = points.map(({ t, ...point }) => {
    const percent = Math.min(((t - start) / span) * 100, 100);
    return { point, percent, x: (percent / 100) * width, w: labelWidth(point.date, point.what) };
  });

  interface Slot {
    side: 'up' | 'down';
    level: number;
    align: 'start' | 'end';
    x: number;
    a: number;
    b: number;
  }
  const placed: Slot[] = [];
  const fits = (s: Slot) =>
    s.a >= 0 &&
    s.b <= width &&
    placed.every(q => {
      if (q.side !== s.side) return true;
      if (q.level === s.level) return s.b + LABEL_GAP <= q.a || q.b + LABEL_GAP <= s.a;
      const [near, far] = q.level < s.level ? [q, s] : [s, q];
      return far.x <= near.a - LEADER_CLEARANCE || far.x >= near.b + LEADER_CLEARANCE;
    });
  const slots = (i: number): Slot[] => {
    const { x, w } = located[i];
    const sides: Slot['side'][] = i % 2 === 0 ? ['up', 'down'] : ['down', 'up'];
    const out: Slot[] = [];
    for (let level = 1; level <= MAX_LEVEL; level++) {
      for (const side of sides) {
        for (const align of ['end', 'start'] as const) {
          const [a, b] = align === 'start' ? [x, x + w] : [x - w, x];
          out.push({ side, level, align, x, a, b });
        }
      }
    }
    return out;
  };
  let budget = 5000;
  const search = (i: number): boolean => {
    if (i === located.length) return true;
    for (const slot of slots(i)) {
      if (--budget < 0) return false;
      if (!fits(slot)) continue;
      placed.push(slot);
      if (search(i + 1)) return true;
      placed.pop();
    }
    return false;
  };
  if (!search(0)) {
    placed.length = 0;
    located.forEach(({ x, w }, i) => {
      const align = x + w <= width ? 'start' : 'end';
      const [a, b] = align === 'start' ? [x, x + w] : [x - w, x];
      placed.push({
        side: i % 2 === 0 ? 'up' : 'down',
        level: Math.min(MAX_LEVEL, 1 + Math.floor(i / 2)),
        align,
        x,
        a,
        b,
      });
    });
  }
  return located.map(({ point, percent }, i) => {
    const { side, level, align } = placed[i];
    return { ...point, percent, side, level, align };
  });
}
