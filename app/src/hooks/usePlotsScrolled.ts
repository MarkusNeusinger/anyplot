/**
 * `plots_scrolled`: how far a visitor got through the gallery, once per visit to `/plots`.
 *
 * The gallery loads its results in batches while the visitor scrolls, so the page has no fixed
 * height and Plausible's own scroll depth says nothing about it. This event reports the deepest
 * point of the visit instead, as a share of the result list it was reached in, with that list's
 * size and whether it was filtered (docs/reference/plausible.md, "Feature usage").
 *
 * One event per visit, sent when the visit ends: the page unmounts, or the tab goes away
 * (`pagehide`). A visitor who never scrolled sends none, so the event's visitors are the ones
 * who looked past the first screen. The offset the page itself restores from an earlier visit
 * is no scrolling of this one: only a point below it counts.
 */

import { useEffect, useRef } from 'react';

import { buildPlausibleUrl, type TrackEvent } from 'src/hooks/useAnalytics';
import { isPlotsPath } from 'src/routes/paths';
import { galleryScrollPercent } from 'src/utils/galleryScroll';

/** The share of the result list above the deepest point, as a band of percent. */
export function shareBand(percent: number): string {
  if (percent < 10) return '0-10';
  if (percent < 25) return '10-25';
  if (percent < 50) return '25-50';
  if (percent < 75) return '50-75';
  return '75-100';
}

/** The size of the result list, as a band of result counts. */
export function resultsBand(total: number): string {
  if (total < 25) return '1-24';
  if (total < 100) return '25-99';
  if (total < 1000) return '100-999';
  return '1000+';
}

interface UsePlotsScrolledOptions {
  /** Results the page holds now. */
  displayedCount: number;
  /** Results the list has in all. */
  total: number;
  filtered: boolean;
  /** The list for the filters in the address is not there yet. */
  loading: boolean;
  /** The offset the page restores from an earlier visit, as it stood when this visit began. */
  restoredOffset: number;
  onTrackEvent: TrackEvent;
}

interface Deepest {
  percent: number;
  total: number;
  filtered: boolean;
  /** The page as Plausible knows it: the event is sent after the visitor left it. */
  url: string;
}

export function usePlotsScrolled({
  displayedCount,
  total,
  filtered,
  loading,
  restoredOffset,
  onTrackEvent,
}: UsePlotsScrolledOptions): void {
  // The list and the callback through refs, the offset from the first render only: the effect
  // must live as long as the visit, and its cleanup is what sends the event. Saving the scroll
  // position for the next visit re-renders the page with a new offset just before it unmounts.
  const list = useRef({ displayedCount, total, filtered, loading });
  list.current = { displayedCount, total, filtered, loading };
  const track = useRef(onTrackEvent);
  track.current = onTrackEvent;
  const floor = useRef(restoredOffset);

  useEffect(() => {
    let deepest: Deepest | null = null;
    let sent = false;

    const sample = () => {
      // The address moves on before this page unmounts, and the next page's scroll reset or
      // clamped offset still reaches this listener: that is no scrolling of the gallery.
      if (!isPlotsPath(window.location.pathname)) return;
      const now = list.current;
      // While new filters load, the address and `filtered` are the new list's and the counts
      // still the old one's: a sample then would describe a list that never existed.
      if (now.loading || now.total === 0 || window.scrollY <= floor.current) return;
      const percent = galleryScrollPercent({
        scrollY: window.scrollY,
        docHeight: document.documentElement.scrollHeight,
        viewportHeight: window.innerHeight,
        displayedCount: now.displayedCount,
        total: now.total,
      });
      if (deepest && percent < deepest.percent) return;
      deepest = { percent, total: now.total, filtered: now.filtered, url: buildPlausibleUrl() };
    };

    const send = () => {
      if (sent || !deepest) return;
      sent = true;
      track.current(
        'plots_scrolled',
        {
          share: shareBand(deepest.percent),
          results: resultsBand(deepest.total),
          filtered: String(deepest.filtered),
        },
        deepest.url
      );
    };

    window.addEventListener('scroll', sample, { passive: true });
    window.addEventListener('pagehide', send);
    return () => {
      window.removeEventListener('scroll', sample);
      window.removeEventListener('pagehide', send);
      send();
    };
  }, []);
}
