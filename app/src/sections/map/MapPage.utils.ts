import type { MapLink } from 'src/pages/MapPage.helpers';
import { colors } from 'src/theme';

export const visuallyHiddenSx = {
  position: 'absolute' as const,
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap' as const,
  border: 0,
};

export function linkEndId(end: MapLink['source']): string | undefined {
  if (typeof end === 'string') return end;
  return (end as { id?: string })?.id;
}

export function strokeFor(isDark: boolean, isHover: boolean, color: string | null): string {
  if (isHover) return color ?? colors.primary;
  if (color) return color;
  return isDark ? 'rgba(240,239,232,0.18)' : 'rgba(26,26,23,0.18)';
}
