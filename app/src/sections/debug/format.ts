/** Formatting helpers of the debug page and its agent cases section. */

/** A timestamp as `12s ago`, `3h ago`, `5d ago`, ...; `—` for one that does not parse. */
export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diffSec = Math.max(0, (Date.now() - then) / 1000);
  if (diffSec < 60) return `${Math.floor(diffSec)}s ago`;
  const diffMin = diffSec / 60;
  if (diffMin < 60) return `${Math.floor(diffMin)}m ago`;
  const diffHr = diffMin / 60;
  if (diffHr < 24) return `${Math.floor(diffHr)}h ago`;
  const diffDay = diffHr / 24;
  if (diffDay < 30) return `${Math.floor(diffDay)}d ago`;
  const diffMon = diffDay / 30;
  if (diffMon < 12) return `${Math.floor(diffMon)}mo ago`;
  return `${Math.floor(diffMon / 12)}y ago`;
}

/** A UTC timestamp as `2026-10-12 14:30:05 UTC`; the input unchanged when it does not parse. */
export function formatUtc(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toISOString().slice(0, 19).replace('T', ' ')} UTC`;
}
