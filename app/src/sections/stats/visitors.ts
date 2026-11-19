/**
 * The answer of `GET /insights/visitors` (`api/routers/insights.py`) and its client-side check:
 * the stats page's visitors tile draws only what passes it.
 */

export interface VisitorPoint {
  date: string;
  /** Unique visitors of the day, as Plausible counts them. */
  visitors: number;
  /** The day's visits; `null` when the answer names none (an API revision older than the page). */
  visits: number | null;
  /**
   * The day's unique visitors who stayed ten seconds and did something, a pointer, a finger or a
   * key, before the ten seconds or after them. `null` for a day before the counting began, for
   * an answer that could not count them, and for an answer that names none.
   */
  engaged: number | null;
}

export interface VisitorsAnswer {
  /** The window's UTC days, oldest first. */
  points: VisitorPoint[];
  /** The first day that has engaged visitors; `null` when the answer names none. */
  engagedSince: string | null;
}

/**
 * What the word "all" carries as its hint in the tile's line of all visitors: read alone, the
 * larger number looks like the audience, and a part of it is no reader at all.
 */
export const ALL_VISITORS_HINT =
  'every unique visitor Plausible counted. a visitor who left within ten seconds or did nothing is in here too: a reader who found what they came for, or automated traffic that runs the page’s scripts.';

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

/** A count, or `null` for anything but a number. */
const countOrNull = (value: unknown): number | null =>
  typeof value === 'number' ? count(value) : null;

const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

/**
 * The answer as the tile reads it: the days it can draw, empty for an answer without any (no
 * Plausible key, an outage). An answer of an API revision older than the page has visitors
 * only, and reads as days without visits and without engaged visitors.
 */
export function readVisitors(body: unknown): VisitorsAnswer {
  const record = body && typeof body === 'object' ? (body as Record<string, unknown>) : {};
  const points = (Array.isArray(record.points) ? record.points : [])
    .filter(
      (point): point is Record<string, unknown> =>
        !!point && typeof point === 'object' && typeof point.date === 'string'
    )
    .map(point => {
      const visitors = count(point.visitors);
      const engaged = countOrNull(point.engaged);
      return {
        date: point.date as string,
        visitors,
        visits: countOrNull(point.visits),
        // Never more than the day's visitors, of whom they are a part.
        engaged: engaged === null ? null : Math.min(engaged, visitors),
      };
    });
  const since = record.engaged_since;
  return {
    points,
    engagedSince: typeof since === 'string' && ISO_DAY.test(since) ? since : null,
  };
}

/** The sums the tile shows once the whole window has engaged visitors. */
export interface EngagedDays {
  /** Unique visitors per day who stayed ten seconds and did something, over the counted days. */
  engaged: number;
  /** All unique visitors per day over the same days. */
  visitors: number;
}

/**
 * The sums over the days that have engaged visitors, once the whole window is counted: its first
 * day is on or after the day the counting began. `null` before that, and for an answer that
 * names no such day (an older API revision) or counts none of them: the tile then draws the
 * unique visitors, so it never shows a strip that is empty for the days it has no number for.
 */
export function engagedDays({ points, engagedSince }: VisitorsAnswer): EngagedDays | null {
  if (engagedSince === null || points.length === 0 || points[0].date < engagedSince) return null;
  const counted = points.filter(point => point.engaged !== null);
  if (counted.length === 0) return null;
  return {
    engaged: counted.reduce((sum, point) => sum + (point.engaged ?? 0), 0),
    visitors: counted.reduce((sum, point) => sum + point.visitors, 0),
  };
}
