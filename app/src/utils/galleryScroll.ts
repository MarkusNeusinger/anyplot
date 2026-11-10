interface GalleryScroll {
  scrollY: number;
  docHeight: number;
  viewportHeight: number;
  /** Results the page holds now. */
  displayedCount: number;
  /** Results the list has in all. */
  total: number;
}

/**
 * How far down the gallery's result list the page is scrolled, in whole percent (0 to 100).
 *
 * The list loads in batches while the visitor scrolls, so the document holds only part of it:
 * the scrollable height is scaled up by the share that is loaded. The filter bar shows this
 * number, and `plots_scrolled` reports it (`usePlotsScrolled`).
 */
export function galleryScrollPercent({
  scrollY,
  docHeight,
  viewportHeight,
  displayedCount,
  total,
}: GalleryScroll): number {
  const loadRatio = displayedCount > 0 && total > 0 ? total / displayedCount : 1;
  const estimatedTotalHeight = (docHeight - viewportHeight) * loadRatio;
  const percent = Math.round((scrollY / estimatedTotalHeight) * 100);
  return Math.min(100, Math.max(0, percent || 0));
}
