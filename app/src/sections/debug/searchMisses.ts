/**
 * The answer of `GET /debug/search-misses` (`api/search_misses.py`): the gallery searches that
 * found nothing in the whole catalogue, per text, over the retention window. Read for the debug
 * page's section (`SearchMissesSection.tsx`).
 */

/** One text: how often it was searched, and on which UTC days first and last. */
export interface SearchMiss {
  query: string;
  count: number;
  first_day: string;
  last_day: string;
}

export interface SearchMisses {
  status: 'ok';
  /** How many days a text is kept before the API deletes it. */
  retention_days: number;
  /** How many different texts the window holds; `misses` may list fewer. */
  texts: number;
  /** Most searched first. */
  misses: SearchMiss[];
}

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isInteger(value) && value > 0 ? value : 0;

const isDay = (value: unknown): value is string =>
  typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);

/**
 * The answer as the section reads it: the list, the status of an answer without one (so the
 * section can say which it is), and `null` for anything else. An entry without a text or a day
 * is left out.
 */
export function readSearchMisses(
  body: unknown
): SearchMisses | 'not_configured' | 'unavailable' | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (record.status === 'not_configured' || record.status === 'unavailable') return record.status;
  if (record.status !== 'ok' || !Array.isArray(record.misses)) return null;
  const misses = record.misses
    .filter(
      (entry): entry is Record<string, unknown> => Boolean(entry) && typeof entry === 'object'
    )
    .filter(
      entry =>
        typeof entry.query === 'string' &&
        entry.query !== '' &&
        isDay(entry.first_day) &&
        isDay(entry.last_day)
    )
    .map(entry => ({
      query: entry.query as string,
      count: count(entry.count),
      first_day: entry.first_day as string,
      last_day: entry.last_day as string,
    }));
  return {
    status: 'ok',
    retention_days: count(record.retention_days),
    texts: Math.max(count(record.texts), misses.length),
    misses,
  };
}
