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
  /**
   * The part of the shares whose fetch Cloudflare verified as a bot it knows, never more than
   * `shares`. `null` when the answer names no verdict (an API revision older than the page).
   */
  verified: number | null;
}

/** A platform with the shares one of the tile's lines gives it. */
export interface SharedLinksPart {
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

/** A spec's shares: its hub and all of its implementation pages together. */
export interface SharedLinksSpec {
  spec_id: string;
  shares: number;
}

/** A library's shares: its implementation pages, whatever the spec. */
export interface SharedLinksLibrary {
  library: string;
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
  /** The most shared specs, largest first. */
  top_specs: SharedLinksSpec[];
  /**
   * The most shared libraries, largest first. A share of a spec's hub counts for no library, so
   * these add up to less than the specs.
   */
  top_libraries: SharedLinksLibrary[];
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

/** A counted part of *whole*: never more than it, and `null` for anything but a number. */
const part = (value: unknown, whole: number): number | null =>
  typeof value === 'number' ? Math.min(count(value), whole) : null;

/**
 * The platforms' shares told apart by Cloudflare's verdict on each fetch: the verified part
 * per platform, largest first, and the rest as one sum. Without a verdict a platform's name
 * is only what the client wrote, so the rest is counted and stands under no name, like the
 * unverified requests of the machine readers tile. `null` when a platform comes without a
 * verdict, so the tile calls no share unverified that it knows nothing about.
 */
export function byVerdict(
  platforms: SharedLinksPlatform[]
): { verified: SharedLinksPart[]; unverified: number } | null {
  const verified: SharedLinksPart[] = [];
  let unverified = 0;
  for (const entry of platforms) {
    if (entry.verified === null) return null;
    if (entry.verified > 0) verified.push({ platform: entry.platform, shares: entry.verified });
    unverified += entry.shares - entry.verified;
  }
  // A stable sort: platforms with the same part keep the answer's order.
  return { verified: verified.sort((a, b) => b.shares - a.shares), unverified };
}

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
  /** The most shared plot pages, largest first: a hub and each implementation on their own. */
  top: SharedLinksPlot[];
  /** Preview images fetched by a client that is neither a preview platform nor a known crawler. */
  other: number;
  /**
   * How many of `other` Cloudflare verified as a bot it knows: a platform the list lacks.
   * `null` when the answer does not say (an API revision older than the page).
   */
  other_verified: number | null;
}

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
  return (
    numbers && {
      ...numbers,
      top: records(record.top)
        .filter(entry => text(entry.spec_id) !== null && count(entry.shares) > 0)
        .map(entry => ({
          spec_id: entry.spec_id as string,
          language: text(entry.language),
          library: text(entry.library),
          shares: count(entry.shares),
        })),
      other: count(record.other),
      other_verified: part(record.other_verified, count(record.other)),
    }
  );
}

/**
 * The answer as the tile reads it; `null` for anything but an `ok` answer with days. An answer
 * without the two lists (an API revision older than the page) reads as one with empty lists,
 * and a platform without its verified part as one with no verdict.
 */
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
      .map(entry => ({
        platform: entry.platform as string,
        shares: count(entry.shares),
        verified: part(entry.verified, count(entry.shares)),
      })),
    top_specs: records(record.top_specs)
      .filter(entry => text(entry.spec_id) !== null && count(entry.shares) > 0)
      .map(entry => ({ spec_id: entry.spec_id as string, shares: count(entry.shares) })),
    top_libraries: records(record.top_libraries)
      .filter(entry => text(entry.library) !== null && count(entry.shares) > 0)
      .map(entry => ({ library: entry.library as string, shares: count(entry.shares) })),
  };
}
