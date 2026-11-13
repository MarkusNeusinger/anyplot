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
   * The day's visits with a second page or an interaction: the ones Plausible does not count as
   * bounced. `null` for a day before the counting began, and for an answer that names none.
   */
  engaged: number | null;
}

export interface VisitorsAnswer {
  /** The window's UTC days, oldest first. */
  points: VisitorPoint[];
  /** The first day that has engaged visits; `null` when the answer names none. */
  engagedSince: string | null;
}

/**
 * What the word "all" carries as its hint in the tile's line of all visits: read alone, the
 * larger number looks like the audience, and a part of it is no reader at all.
 */
export const ALL_VISITS_HINT =
  'every visit Plausible counted. a visit of one page without a click is in here too: a reader who found what they came for, or automated traffic that runs the page’s scripts.';

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

/** A count, or `null` for anything but a number. */
const countOrNull = (value: unknown): number | null =>
  typeof value === 'number' ? count(value) : null;

const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

/**
 * The answer as the tile reads it: the days it can draw, empty for an answer without any (no
 * Plausible key, an outage). An answer of an API revision older than the page has visitors
 * only, and reads as days without visits and without engaged visits.
 */
export function readVisitors(body: unknown): VisitorsAnswer {
  const record = body && typeof body === 'object' ? (body as Record<string, unknown>) : {};
  const points = (Array.isArray(record.points) ? record.points : [])
    .filter(
      (point): point is Record<string, unknown> =>
        !!point && typeof point === 'object' && typeof point.date === 'string'
    )
    .map(point => {
      const visits = countOrNull(point.visits);
      const engaged = countOrNull(point.engaged);
      return {
        date: point.date as string,
        visitors: count(point.visitors),
        visits,
        // Never more than the day's visits, of which they are a part.
        engaged: engaged === null || visits === null ? null : Math.min(engaged, visits),
      };
    });
  const since = record.engaged_since;
  return {
    points,
    engagedSince: typeof since === 'string' && ISO_DAY.test(since) ? since : null,
  };
}

/** The days that have engaged visits, with the sums the tile shows for them. */
export interface EngagedDays {
  /** Visits with a second page or an interaction, over the counted days. */
  engaged: number;
  /** All visits over the same days. */
  visits: number;
  /** Whether the window's first day is counted: if not, the tile names the day counting began. */
  wholeWindow: boolean;
}

/**
 * The sums over the days that have engaged visits; `null` when no day has them, which is an
 * answer of an older API revision, and the tile then draws the visitors as before.
 */
export function engagedDays(points: VisitorPoint[]): EngagedDays | null {
  const counted = points.filter(point => point.engaged !== null && point.visits !== null);
  if (counted.length === 0) return null;
  return {
    engaged: counted.reduce((sum, point) => sum + (point.engaged ?? 0), 0),
    visits: counted.reduce((sum, point) => sum + (point.visits ?? 0), 0),
    wholeWindow: points[0]?.engaged !== null,
  };
}
