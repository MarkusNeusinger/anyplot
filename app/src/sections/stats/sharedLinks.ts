/**
 * The answer of `GET /insights/shared-links` (`api/shared_links.py`) and its
 * client-side check: the stats page's shared links tile draws only what
 * passes it.
 */

export interface SharedLinksDay {
  date: string;
  shares: number;
}

export interface SharedLinksPlatform {
  platform: string;
  shares: number;
}

/** A plot page: a spec's hub (no language, no library) or one implementation of it. */
export interface SharedLinksPlot {
  spec_id: string;
  language: string | null;
  library: string | null;
  shares: number;
}

export interface SharedLinksResponse {
  status: 'ok' | 'not_configured' | 'unavailable';
  window_days: number;
  total: number;
  /** The window's UTC days, oldest first; empty unless `status` is `ok`. */
  days: SharedLinksDay[];
  /** Largest first. */
  platforms: SharedLinksPlatform[];
  /** The most shared plot pages, largest first. */
  top: SharedLinksPlot[];
}

/**
 * The names the tile shows where the stored one says less than it should. `whatsapp-lite` is an
 * app that signs as WhatsApp without its version, which is what Signal does.
 */
const PLATFORM_LABELS: Record<string, string> = {
  'whatsapp-lite': 'signal & similar',
};

export function platformLabel(platform: string): string {
  return PLATFORM_LABELS[platform] ?? platform;
}

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

const text = (value: unknown): string | null =>
  typeof value === 'string' && value !== '' ? value : null;

const records = (value: unknown): Record<string, unknown>[] =>
  Array.isArray(value)
    ? value.filter(
        (entry): entry is Record<string, unknown> => !!entry && typeof entry === 'object'
      )
    : [];

/** The answer of `GET /debug/shared-links`: the public numbers plus what they leave out. */
export interface SharedLinksDetail extends SharedLinksResponse {
  /** Preview images fetched by a client that is neither a preview platform nor a known crawler. */
  other: number;
  /**
   * Per platform, and for `other`, how many of its fetches Cloudflare verified as a bot it
   * knows. A platform with none is absent.
   */
  verified: Record<string, number>;
}

const counts = (value: unknown): Record<string, number> =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? Object.fromEntries(
        Object.entries(value)
          .map(([name, entry]): [string, number] => [name, count(entry)])
          .filter(([, entry]) => entry > 0)
      )
    : {};

/**
 * The detail as the debug section reads it: the numbers for `ok`, the status itself for an
 * answer without numbers, so the section can say which it is, and `null` for anything else.
 */
export function readSharedLinksDetail(
  body: unknown
): SharedLinksDetail | 'not_configured' | 'unavailable' | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (record.status === 'not_configured' || record.status === 'unavailable') return record.status;
  const numbers = readSharedLinks(body);
  return numbers && { ...numbers, other: count(record.other), verified: counts(record.verified) };
}

/** The answer as the tile reads it; `null` for anything but an `ok` answer with days. */
export function readSharedLinks(body: unknown): SharedLinksResponse | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (record.status !== 'ok') return null;
  const days = records(record.days)
    .filter(day => typeof day.date === 'string')
    .map(day => ({ date: day.date as string, shares: count(day.shares) }));
  if (days.length === 0) return null;
  return {
    status: 'ok',
    window_days: count(record.window_days),
    total: count(record.total),
    days,
    platforms: records(record.platforms)
      .filter(entry => text(entry.platform) !== null && count(entry.shares) > 0)
      .map(entry => ({ platform: entry.platform as string, shares: count(entry.shares) })),
    top: records(record.top)
      .filter(entry => text(entry.spec_id) !== null && count(entry.shares) > 0)
      .map(entry => ({
        spec_id: entry.spec_id as string,
        language: text(entry.language),
        library: text(entry.library),
        shares: count(entry.shares),
      })),
  };
}
