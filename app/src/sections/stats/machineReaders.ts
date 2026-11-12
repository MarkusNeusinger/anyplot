/**
 * The answer of `GET /insights/machine-readers` (`api/machine_reads_query.py`)
 * and its client-side check: the stats page's machine readers tile draws only
 * what passes it.
 */

export interface MachineReaderPoint {
  date: string;
  for_person: number;
  index_training: number;
  search: number;
  mcp: number;
}

export interface MachineReaderTotals {
  for_person: number;
  index_training: number;
  search: number;
  /** MCP requests of every client, verified or not. */
  mcp: number;
  /** Served reads in the tile's audiences by a named vendor Cloudflare did not verify. */
  unverified: number;
}

export interface MachineReadersResponse {
  status: 'ok' | 'not_configured' | 'unavailable';
  days: number;
  /** The 28 UTC days, oldest first; empty unless `status` is `ok`. */
  points: MachineReaderPoint[];
  totals: MachineReaderTotals;
  generated_at: string | null;
}

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

/** The answer as the tile reads it; `null` for anything but an `ok` answer with days. */
export function readMachineReaders(body: unknown): MachineReadersResponse | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (record.status !== 'ok' || !Array.isArray(record.points)) return null;
  const points = record.points
    .filter(
      (point): point is Record<string, unknown> =>
        !!point &&
        typeof point === 'object' &&
        typeof (point as MachineReaderPoint).date === 'string'
    )
    .map(point => ({
      date: point.date as string,
      for_person: count(point.for_person),
      index_training: count(point.index_training),
      search: count(point.search),
      mcp: count(point.mcp),
    }));
  if (points.length === 0) return null;
  const totals = (
    record.totals && typeof record.totals === 'object' ? record.totals : {}
  ) as Record<string, unknown>;
  return {
    status: 'ok',
    days: count(record.days),
    points,
    totals: {
      for_person: count(totals.for_person),
      index_training: count(totals.index_training),
      search: count(totals.search),
      mcp: count(totals.mcp),
      unverified: count(totals.unverified),
    },
    generated_at: typeof record.generated_at === 'string' ? record.generated_at : null,
  };
}
