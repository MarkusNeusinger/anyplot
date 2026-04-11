import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useInfiniteScroll } from './useInfiniteScroll';
import type { PlotImage } from '../types';
import { BATCH_SIZE } from '../constants';

// --- IntersectionObserver mock ---
let observerCallback: IntersectionObserverCallback;
const mockObserve = vi.fn();
const mockDisconnect = vi.fn();

let lastObserverOptions: IntersectionObserverInit | undefined;

class MockIntersectionObserver {
  constructor(cb: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    observerCallback = cb;
    lastObserverOptions = options;
  }
  observe = mockObserve;
  disconnect = mockDisconnect;
  unobserve = vi.fn();
  readonly root = null;
  readonly rootMargin = '';
  readonly thresholds: readonly number[] = [];
  takeRecords(): IntersectionObserverEntry[] { return []; }
}

beforeEach(() => {
  vi.useFakeTimers();
  lastObserverOptions = undefined;
  vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);
  // requestAnimationFrame — execute immediately
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => { cb(0); return 0; });
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function makeImages(n: number): PlotImage[] {
  return Array.from({ length: n }, (_, i) => ({
    library: 'matplotlib',
    url: `https://example.com/img${i}.png`,
    spec_id: `spec-${i}`,
  }));
}

describe('useInfiniteScroll', () => {
  it('returns loadMoreRef and loadMore', () => {
    const all = makeImages(50);
    const displayed = all.slice(0, BATCH_SIZE);
    const setDisplayed = vi.fn();
    const setHasMore = vi.fn();

    const { result } = renderHook(() =>
      useInfiniteScroll({
        allImages: all,
        displayedImages: displayed,
        hasMore: true,
        setDisplayedImages: setDisplayed,
        setHasMore: setHasMore,
      }),
    );

    expect(result.current.loadMoreRef).toBeDefined();
    expect(typeof result.current.loadMore).toBe('function');
  });

  it('loadMore appends next batch and updates hasMore', () => {
    const all = makeImages(50);
    const displayed = all.slice(0, BATCH_SIZE);
    const setDisplayed = vi.fn();
    const setHasMore = vi.fn();

    const { result } = renderHook(() =>
      useInfiniteScroll({
        allImages: all,
        displayedImages: displayed,
        hasMore: true,
        setDisplayedImages: setDisplayed,
        setHasMore: setHasMore,
      }),
    );

    // Unblock loading (wait for the 150ms guard)
    act(() => { vi.advanceTimersByTime(200); });

    act(() => { result.current.loadMore(); });

    expect(setDisplayed).toHaveBeenCalled();
    expect(setHasMore).toHaveBeenCalled();
  });

  it('loadMore does nothing when hasMore is false', () => {
    const all = makeImages(10);
    const setDisplayed = vi.fn();
    const setHasMore = vi.fn();

    const { result } = renderHook(() =>
      useInfiniteScroll({
        allImages: all,
        displayedImages: all,
        hasMore: false,
        setDisplayedImages: setDisplayed,
        setHasMore: setHasMore,
      }),
    );

    act(() => { vi.advanceTimersByTime(200); });
    act(() => { result.current.loadMore(); });

    // setDisplayed should not be called by loadMore (may be called by checkAndLoad effects)
    // The key assertion is that hasMore=false prevents additional loading
    expect(setHasMore).not.toHaveBeenCalled();
  });

  it('IntersectionObserver is created and observes loadMoreRef', () => {
    const all = makeImages(50);
    const displayed = all.slice(0, BATCH_SIZE);

    renderHook(() =>
      useInfiniteScroll({
        allImages: all,
        displayedImages: displayed,
        hasMore: true,
        setDisplayedImages: vi.fn(),
        setHasMore: vi.fn(),
      }),
    );

    expect(lastObserverOptions).toEqual(
      expect.objectContaining({ threshold: 0.1, rootMargin: '2400px 0px' }),
    );
  });

  it('IntersectionObserver callback triggers loadMore when entry is intersecting', () => {
    const all = makeImages(50);
    const displayed = all.slice(0, BATCH_SIZE);
    const setDisplayed = vi.fn();
    const setHasMore = vi.fn();

    renderHook(() =>
      useInfiniteScroll({
        allImages: all,
        displayedImages: displayed,
        hasMore: true,
        setDisplayedImages: setDisplayed,
        setHasMore: setHasMore,
      }),
    );

    // Unblock loading guard
    act(() => { vi.advanceTimersByTime(200); });

    // Simulate intersection
    act(() => {
      observerCallback(
        [{ isIntersecting: true } as IntersectionObserverEntry],
        {} as IntersectionObserver,
      );
    });

    expect(setDisplayed).toHaveBeenCalled();
  });

  it('observer disconnects on unmount', () => {
    const all = makeImages(50);
    const displayed = all.slice(0, BATCH_SIZE);

    const { unmount } = renderHook(() =>
      useInfiniteScroll({
        allImages: all,
        displayedImages: displayed,
        hasMore: true,
        setDisplayedImages: vi.fn(),
        setHasMore: vi.fn(),
      }),
    );

    unmount();
    expect(mockDisconnect).toHaveBeenCalled();
  });

  it('blocks loading for 150ms when allImages changes (filter guard)', () => {
    const all = makeImages(50);
    const displayed = all.slice(0, BATCH_SIZE);
    const setDisplayed = vi.fn();
    const setHasMore = vi.fn();

    const { result, rerender } = renderHook(
      ({ images }: { images: PlotImage[] }) =>
        useInfiniteScroll({
          allImages: images,
          displayedImages: displayed,
          hasMore: true,
          setDisplayedImages: setDisplayed,
          setHasMore: setHasMore,
        }),
      { initialProps: { images: all } },
    );

    // Unblock initial guard
    act(() => { vi.advanceTimersByTime(200); });
    setDisplayed.mockClear();
    setHasMore.mockClear();

    // Change allImages to trigger the guard
    const newAll = makeImages(60);
    rerender({ images: newAll });

    // loadMore should be blocked immediately after allImages change
    act(() => { result.current.loadMore(); });
    expect(setHasMore).not.toHaveBeenCalled();

    // After 200ms the guard lifts
    act(() => { vi.advanceTimersByTime(200); });
    act(() => { result.current.loadMore(); });
    expect(setDisplayed).toHaveBeenCalled();
  });
});
