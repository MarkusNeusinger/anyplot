/**
 * The answer of `GET /debug/search-misses` (`api/search_misses.py`): one page of the gallery
 * searches that found nothing in the whole catalogue, per text, over the retention window, and
 * the days that reached the day's cap. Read for the debug page's section
 * (`SearchMissesSection.tsx`).
 */

/** One text: how often it was searched, and on which UTC days first and last. */
export interface SearchMiss {
  query: string;
  count: number;
  first_day: string;
  last_day: string;
}

/** The two orders of the list: most searched first, or most recently searched first. */
export type SearchMissOrder = 'count' | 'recent';

export interface SearchMisses {
  status: 'ok';
  /** How many days a text is kept before the API deletes it. */
  retention_days: number;
  /** How many new texts a UTC day takes before a new one is dropped. */
  day_cap: number;
  order: SearchMissOrder;
  /** Where in the whole list this page starts. */
  offset: number;
  /** How many different texts the window holds; a page lists fewer. */
  texts: number;
  misses: SearchMiss[];
  /** The UTC days, newest first, that reached `day_cap`: on those a new text was dropped. */
  capped_days: string[];
}

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isInteger(value) && value > 0 ? value : 0;

const isDay = (value: unknown): value is string =>
  typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);

/** The entries of one page; an entry without a text or a day is left out. */
function readEntries(value: unknown): SearchMiss[] {
  if (!Array.isArray(value)) return [];
  return value
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
}

/**
 * The answer as the section reads it: the page, the status of an answer without one (so the
 * section can say which it is), and `null` for anything else. A missing order reads as `count`,
 * missing capped days as none.
 */
export function readSearchMisses(
  body: unknown
): SearchMisses | 'not_configured' | 'unavailable' | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (record.status === 'not_configured' || record.status === 'unavailable') return record.status;
  if (record.status !== 'ok' || !Array.isArray(record.misses)) return null;
  const misses = readEntries(record.misses);
  const offset = count(record.offset);
  return {
    status: 'ok',
    retention_days: count(record.retention_days),
    day_cap: count(record.day_cap),
    order: record.order === 'recent' ? 'recent' : 'count',
    offset,
    texts: Math.max(count(record.texts), offset + misses.length),
    misses,
    capped_days: Array.isArray(record.capped_days) ? record.capped_days.filter(isDay) : [],
  };
}
