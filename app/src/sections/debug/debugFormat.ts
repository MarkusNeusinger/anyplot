import { LIBRARIES } from 'src/constants';
import type { SpecStatus } from 'src/sections/debug/SpecMatrix';
import { colors } from 'src/theme';

export const countImpls = (spec: SpecStatus): number =>
  LIBRARIES.filter(lib => spec[lib as keyof SpecStatus] !== null).length;

export function scoreColor(score: number | null): string {
  if (score === null) return 'var(--ink-muted)';
  if (score >= 90) return colors.success;
  if (score >= 75) return colors.warning;
  return colors.error;
}

export function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function formatDateShort(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function pingColor(ms: number): string {
  if (ms < 75) return colors.success;
  if (ms < 200) return colors.warning;
  return colors.error;
}
