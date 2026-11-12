/**
 * What the stats page's day strips share: one bar per UTC day of a 28-day window, for the
 * visitors, the machine readers, the shared links and the timeline. The same height, the same
 * floor and the same green, so the strips read as one family and a day's bar means the same in
 * each.
 */

import { colors } from 'src/theme';

/** A strip's height, in px. */
export const CHART_PX = 70;
/** The floor every day's bar is drawn with (3% of the strip). */
export const MIN_BAR_PX = CHART_PX * 0.03;

/**
 * The green of every strip's bars, with its strength at rest and under the pointer or the
 * keyboard focus. At rest a bar is below 3:1 against the page on purpose, as a quiet strip: the
 * window's sums stand in text beside it, and each day's number is its column's name and tooltip.
 */
export const STRIP_BAR = { color: colors.primaryDark, opacity: 0.5, activeOpacity: 0.8 } as const;

/**
 * A day's bar height in px, the only thing that encodes its number: proportional to it, the
 * busiest day filling the strip, and one floor for every day, so a busier day is never shorter.
 * A day without anything draws the floor.
 */
export function columnPx(total: number, maxTotal: number): number {
  if (total <= 0 || maxTotal <= 0) return MIN_BAR_PX;
  return Math.max((Math.min(total, maxTotal) / maxTotal) * CHART_PX, MIN_BAR_PX);
}
