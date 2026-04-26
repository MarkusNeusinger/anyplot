import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useLatestRelease } from './useLatestRelease';

const CACHE_KEY = 'anyplot:latest-release';
const ONE_HOUR = 60 * 60 * 1000;

function mockFetchTag(tag: string, ok = true) {
  (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
    ok,
    json: () => Promise.resolve({ tag_name: tag }),
  });
}

describe('useLatestRelease', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.spyOn(globalThis, 'fetch');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns the cached tag immediately when cache is fresh', () => {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: 'v2.1', ts: Date.now() }));
    const { result } = renderHook(() => useLatestRelease());
    expect(result.current).toBe('v2.1');
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('renders the stale cached tag immediately and refreshes in the background', async () => {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: 'v2.0', ts: Date.now() - ONE_HOUR - 1000 }));
    mockFetchTag('v2.1');

    const { result } = renderHook(() => useLatestRelease());
    expect(result.current).toBe('v2.0');

    await waitFor(() => expect(result.current).toBe('v2.1'));
    const stored = JSON.parse(localStorage.getItem(CACHE_KEY)!);
    expect(stored.tag).toBe('v2.1');
  });

  it('fetches on mount when no cache exists', async () => {
    mockFetchTag('v2.1');
    const { result } = renderHook(() => useLatestRelease());
    expect(result.current).toBeNull();

    await waitFor(() => expect(result.current).toBe('v2.1'));
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it('refetches once per hour while mounted', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      mockFetchTag('v2.0');
      const { result } = renderHook(() => useLatestRelease());
      await waitFor(() => expect(result.current).toBe('v2.0'));

      mockFetchTag('v2.1');
      await vi.advanceTimersByTimeAsync(ONE_HOUR + 100);

      await waitFor(() => expect(result.current).toBe('v2.1'));
      expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it('refetches when the tab becomes visible after the cache goes stale', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: 'v2.0', ts: Date.now() - ONE_HOUR - 1000 }));
      mockFetchTag('v2.1');

      const { result } = renderHook(() => useLatestRelease());
      // Wait for the on-mount refresh to complete first.
      await waitFor(() => expect(result.current).toBe('v2.1'));

      // Force the cache stale again, advance past the per-attempt throttle, then fire visibilitychange.
      localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: 'v2.1', ts: Date.now() - ONE_HOUR - 1000 }));
      await vi.advanceTimersByTimeAsync(2 * 60 * 1000);
      mockFetchTag('v2.2');
      Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });
      document.dispatchEvent(new Event('visibilitychange'));

      await waitFor(() => expect(result.current).toBe('v2.2'));
    } finally {
      vi.useRealTimers();
    }
  });

  it('keeps the cached value when the API responds with non-ok', async () => {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: 'v2.0', ts: Date.now() - ONE_HOUR - 1000 }));
    mockFetchTag('ignored', false);

    const { result } = renderHook(() => useLatestRelease());
    expect(result.current).toBe('v2.0');

    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
    expect(result.current).toBe('v2.0');
  });

  it('keeps the cached value when fetch rejects', async () => {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: 'v2.0', ts: Date.now() - ONE_HOUR - 1000 }));
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('offline'));

    const { result } = renderHook(() => useLatestRelease());
    expect(result.current).toBe('v2.0');

    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
    expect(result.current).toBe('v2.0');
  });

  it('ignores corrupted cache entries', async () => {
    localStorage.setItem(CACHE_KEY, 'not-json');
    mockFetchTag('v2.1');
    const { result } = renderHook(() => useLatestRelease());
    expect(result.current).toBeNull();

    await waitFor(() => expect(result.current).toBe('v2.1'));
  });

  it('aborts the in-flight fetch on unmount', () => {
    const { unmount } = renderHook(() => useLatestRelease());
    const signal = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[1]?.signal as
      | AbortSignal
      | undefined;
    expect(signal).toBeDefined();
    unmount();
    expect(signal!.aborted).toBe(true);
  });

  it('throttles refresh attempts when localStorage throws', async () => {
    const setItemSpy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    try {
      mockFetchTag('v2.0');
      renderHook(() => useLatestRelease());

      // Several visibility changes in quick succession should not multiply requests.
      Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });
      for (let i = 0; i < 5; i++) document.dispatchEvent(new Event('visibilitychange'));

      await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
      expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    } finally {
      setItemSpy.mockRestore();
    }
  });
});
