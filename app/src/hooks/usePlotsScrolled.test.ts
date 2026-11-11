import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { resultsBand, shareBand, usePlotsScrolled } from 'src/hooks/usePlotsScrolled';

const VIEWPORT = 1000;

/** The page scrolled to `scrollY` in a document `docHeight` high, as the browser reports it. */
function scrollTo(scrollY: number, docHeight: number) {
  Object.defineProperty(window, 'scrollY', { value: scrollY, configurable: true });
  Object.defineProperty(document.documentElement, 'scrollHeight', {
    value: docHeight,
    configurable: true,
  });
  window.dispatchEvent(new Event('scroll'));
}

interface List {
  displayedCount: number;
  total: number;
  filtered: boolean;
  loading: boolean;
  restoredOffset: number;
}

const ALL: List = {
  displayedCount: 36,
  total: 3600,
  filtered: false,
  loading: false,
  restoredOffset: 0,
};

function visit(list: List = ALL) {
  const onTrackEvent = vi.fn();
  const hook = renderHook((props: List) => usePlotsScrolled({ ...props, onTrackEvent }), {
    initialProps: list,
  });
  return { ...hook, onTrackEvent };
}

describe('usePlotsScrolled', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/plots');
    Object.defineProperty(window, 'innerHeight', { value: VIEWPORT, configurable: true });
    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true });
  });

  afterEach(() => {
    window.history.replaceState({}, '', '/');
  });

  it('sends nothing for a visit that never scrolled', () => {
    const { unmount, onTrackEvent } = visit();
    unmount();
    expect(onTrackEvent).not.toHaveBeenCalled();
  });

  it('sends the deepest point once, when the visitor leaves the page', () => {
    const { unmount, onTrackEvent } = visit();

    // One batch of 36 is on the page, 1 % of the list: its end is 1 % of the way.
    scrollTo(3000, 4000);
    expect(onTrackEvent).not.toHaveBeenCalled();
    // Scrolling back up does not take the depth back.
    scrollTo(200, 4000);

    unmount();
    expect(onTrackEvent).toHaveBeenCalledTimes(1);
    expect(onTrackEvent).toHaveBeenCalledWith(
      'plots_scrolled',
      { share: '0-10', results: '1000+', filtered: 'false' },
      'https://anyplot.ai/plots'
    );
  });

  it('sends it when the tab goes away, and not again when the page unmounts after that', () => {
    const { unmount, onTrackEvent } = visit({ ...ALL, displayedCount: 1800 });
    scrollTo(60_000, 101_000);

    window.dispatchEvent(new Event('pagehide'));
    expect(onTrackEvent).toHaveBeenCalledWith(
      'plots_scrolled',
      { share: '25-50', results: '1000+', filtered: 'false' },
      'https://anyplot.ai/plots'
    );

    // The page came back from the back/forward cache and the visitor went on: still one event.
    scrollTo(100_000, 101_000);
    unmount();
    expect(onTrackEvent).toHaveBeenCalledTimes(1);
  });

  it('reports the list the deepest point was reached in, under the page it was reached on', () => {
    const { rerender, unmount, onTrackEvent } = visit();
    scrollTo(1500, 4000);

    // A filter narrows the list to 40 results, all loaded, and the visitor reaches its end.
    window.history.replaceState({}, '', '/plots?lib=matplotlib');
    rerender({ ...ALL, displayedCount: 40, total: 40, filtered: true });
    scrollTo(3000, 4000);

    // The filter goes again; the top of the full list is no deeper.
    window.history.replaceState({}, '', '/plots');
    rerender(ALL);
    scrollTo(300, 4000);

    unmount();
    expect(onTrackEvent).toHaveBeenCalledWith(
      'plots_scrolled',
      { share: '75-100', results: '25-99', filtered: 'true' },
      'https://anyplot.ai/plots/lib/matplotlib'
    );
  });

  it('does not count the offset the page restores from an earlier visit, only a point below it', () => {
    const restored = visit({ ...ALL, restoredOffset: 2400 });
    // The page puts the visitor back where the last visit ended, and they scroll up from there.
    scrollTo(2400, 4000);
    scrollTo(1200, 4000);
    restored.unmount();
    expect(restored.onTrackEvent).not.toHaveBeenCalled();

    const further = visit({ ...ALL, restoredOffset: 2400 });
    scrollTo(2400, 4000);
    scrollTo(2500, 4000);
    further.unmount();
    expect(further.onTrackEvent).toHaveBeenCalledTimes(1);
  });

  it('keeps the offset the visit began with when the page saves a new one on the way out', () => {
    // A card click saves the scroll position for the next visit, which re-renders the page with
    // that offset just before it unmounts: the event must not go out early, and still go out.
    const { rerender, unmount, onTrackEvent } = visit();
    scrollTo(3000, 4000);

    rerender({ ...ALL, restoredOffset: 3000 });
    expect(onTrackEvent).not.toHaveBeenCalled();

    unmount();
    expect(onTrackEvent).toHaveBeenCalledTimes(1);
  });

  it('ignores a scroll that arrives after the address moved on to the next page', () => {
    // The router changes the address before this page unmounts, and the next page's scroll
    // reset or clamped offset still reaches the listener.
    const { unmount, onTrackEvent } = visit();
    window.history.replaceState({}, '', '/scatter-basic/python/matplotlib');
    scrollTo(900, 1200);
    unmount();
    expect(onTrackEvent).not.toHaveBeenCalled();
  });

  it('sends nothing for an empty list', () => {
    const { unmount, onTrackEvent } = visit({ ...ALL, displayedCount: 0, total: 0 });
    scrollTo(300, 1400);
    unmount();
    expect(onTrackEvent).not.toHaveBeenCalled();
  });

  it('takes no sample while the list for new filters is still loading', () => {
    // The filters and the address change at once, the counts only when the answer is there:
    // a sample in between would report the new filter with the old list's size.
    const { rerender, unmount, onTrackEvent } = visit();
    window.history.replaceState({}, '', '/plots?lib=matplotlib');
    rerender({ ...ALL, filtered: true, loading: true });
    scrollTo(3000, 4000);

    // The answer: 40 results, all on the page, and the visitor is at their top.
    rerender({ ...ALL, displayedCount: 40, total: 40, filtered: true });
    scrollTo(100, 4000);

    unmount();
    expect(onTrackEvent).toHaveBeenCalledWith(
      'plots_scrolled',
      { share: '0-10', results: '25-99', filtered: 'true' },
      'https://anyplot.ai/plots/lib/matplotlib'
    );
  });

  it('counts a gallery opened with a trailing slash', () => {
    // The router serves `/plots/` as it serves `/plots`, and the pageview records both as `/plots`.
    window.history.replaceState({}, '', '/plots/');
    const { unmount, onTrackEvent } = visit();
    scrollTo(3000, 4000);
    unmount();
    expect(onTrackEvent).toHaveBeenCalledWith(
      'plots_scrolled',
      { share: '0-10', results: '1000+', filtered: 'false' },
      'https://anyplot.ai/plots'
    );
  });
});

describe('shareBand', () => {
  it.each([
    [0, '0-10'],
    [9, '0-10'],
    [10, '10-25'],
    [24, '10-25'],
    [25, '25-50'],
    [49, '25-50'],
    [50, '50-75'],
    [74, '50-75'],
    [75, '75-100'],
    [100, '75-100'],
  ])('puts %i %% into %s', (percent, band) => {
    expect(shareBand(percent)).toBe(band);
  });
});

describe('resultsBand', () => {
  it.each([
    [1, '1-24'],
    [24, '1-24'],
    [25, '25-99'],
    [99, '25-99'],
    [100, '100-999'],
    [999, '100-999'],
    [1000, '1000+'],
    [4600, '1000+'],
  ])('puts a list of %i into %s', (total, band) => {
    expect(resultsBand(total)).toBe(band);
  });
});
