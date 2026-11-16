import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FILTER_FETCH_ERROR, useFilterFetch } from 'src/hooks/useFilterFetch';
import type { ActiveFilters, PlotImage } from 'src/types';

describe('useFilterFetch', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockImages: PlotImage[] = Array.from({ length: 50 }, (_, i) => ({
    library: 'matplotlib',
    language: 'python',
    url: `https://example.com/img${i}.png`,
    spec_id: `spec-${i}`,
  }));

  const mockApiResponse = {
    images: mockImages,
    counts: {
      lib: { matplotlib: 50 },
      spec: {},
      plot: {},
      data: {},
      dom: {},
      feat: {},
      dep: {},
      tech: {},
      pat: {},
      prep: {},
      style: {},
    },
    globalCounts: {
      lib: { matplotlib: 50 },
      spec: {},
      plot: {},
      data: {},
      dom: {},
      feat: {},
      dep: {},
      tech: {},
      pat: {},
      prep: {},
      style: {},
    },
    orCounts: [],
    specTitles: { 'spec-0': 'Scatter Plot' },
  };

  describe('initial state', () => {
    it('starts loading when no initialState provided', () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      const { result } = renderHook(() => useFilterFetch({ activeFilters: [] }));
      expect(result.current.loading).toBe(true);
    });

    it('uses provided initial state and skips fetch', () => {
      const initialImages: PlotImage[] = [
        { library: 'seaborn', language: 'python', url: 'test.png' },
      ];

      const { result } = renderHook(() =>
        useFilterFetch({
          activeFilters: [],
          initialState: {
            allImages: initialImages,
            displayedImages: initialImages,
          },
          skipInitialFetch: true,
        })
      );

      expect(result.current.allImages).toEqual(initialImages);
      expect(result.current.loading).toBe(false);
    });
  });

  describe('fetching', () => {
    it('calls fetch with correct URL and signal', async () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      renderHook(() => useFilterFetch({ activeFilters: [] }));

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          expect.stringContaining('/plots/filter'),
          expect.objectContaining({ signal: expect.any(AbortSignal) })
        );
      });
    });

    it('includes filter params in the URL', async () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      const filters: ActiveFilters = [
        { category: 'lib', values: ['matplotlib'] },
        { category: 'plot', values: ['scatter', 'line'] },
      ];

      renderHook(() => useFilterFetch({ activeFilters: filters }));

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalled();
      });

      const fetchUrl = fetchMock.mock.calls[0][0] as string;
      expect(fetchUrl).toContain('lib=matplotlib');
      expect(fetchUrl).toContain('plot=scatter%2Cline');
    });

    it('populates images after successful fetch', async () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      const { result } = renderHook(() => useFilterFetch({ activeFilters: [] }));

      await waitFor(() => {
        expect(result.current.allImages.length).toBe(50);
      });

      // BATCH_SIZE is 36 — display should be paginated
      expect(result.current.displayedImages.length).toBeLessThanOrEqual(36);
      expect(result.current.hasMore).toBe(true);
      expect(result.current.loading).toBe(false);
    });

    it('sets hasMore to false when images fit in one batch', async () => {
      const smallResponse = { ...mockApiResponse, images: mockImages.slice(0, 5) };
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(smallResponse) });

      const { result } = renderHook(() => useFilterFetch({ activeFilters: [] }));

      await waitFor(() => {
        expect(result.current.displayedImages).toHaveLength(5);
      });

      expect(result.current.hasMore).toBe(false);
    });

    it('stores filter counts and spec titles', async () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      const { result } = renderHook(() => useFilterFetch({ activeFilters: [] }));

      await waitFor(() => {
        expect(result.current.filterCounts).not.toBeNull();
      });

      expect(result.current.filterCounts).toEqual(mockApiResponse.counts);
      expect(result.current.specTitles).toEqual({ 'spec-0': 'Scatter Plot' });
    });
  });

  describe('error handling', () => {
    it('sets the short error line on network failure, not the raw exception', async () => {
      fetchMock.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useFilterFetch({ activeFilters: [] }));

      await waitFor(() => {
        expect(result.current.error).toBe(FILTER_FETCH_ERROR);
      });
      expect(result.current.loading).toBe(false);
    });

    it('sets the short error line on a non-ok HTTP response, without status or URL', async () => {
      fetchMock.mockResolvedValue({ ok: false, status: 404, statusText: 'Not Found' });

      const { result } = renderHook(() => useFilterFetch({ activeFilters: [] }));

      await waitFor(() => {
        expect(result.current.error).toBe(FILTER_FETCH_ERROR);
      });
      expect(result.current.error).not.toMatch(/404|plots\/filter|ApiError/);
    });

    it('clears the error when the next filter fetch starts, and keeps it clear on success', async () => {
      // A plain Error and a 404 are not retried by apiGet, so one mock answer is one attempt.
      fetchMock.mockRejectedValueOnce(new Error('Network error'));
      let answer: (value: unknown) => void = () => {};
      fetchMock.mockImplementationOnce(
        () =>
          new Promise(resolve => {
            answer = resolve;
          })
      );

      const { result, rerender } = renderHook(
        ({ filters }: { filters: ActiveFilters }) => useFilterFetch({ activeFilters: filters }),
        { initialProps: { filters: [{ category: 'lib', values: ['bokeh'] }] as ActiveFilters } }
      );
      await waitFor(() => {
        expect(result.current.error).toBe(FILTER_FETCH_ERROR);
      });

      rerender({ filters: [{ category: 'lib', values: ['matplotlib'] }] });
      // The second fetch is still pending: the banner of the first one is already gone.
      await waitFor(() => {
        expect(result.current.loading).toBe(true);
      });
      expect(result.current.error).toBe('');

      answer({ ok: true, json: () => Promise.resolve(mockApiResponse) });
      await waitFor(() => {
        expect(result.current.allImages).toHaveLength(50);
      });
      expect(result.current.error).toBe('');
      expect(result.current.loading).toBe(false);
    });

    it('drops the plots of the previous filter when the next filter fails', async () => {
      fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockApiResponse) });
      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      const { result, rerender } = renderHook(
        ({ filters }: { filters: ActiveFilters }) => useFilterFetch({ activeFilters: filters }),
        {
          initialProps: { filters: [{ category: 'lib', values: ['matplotlib'] }] as ActiveFilters },
        }
      );
      await waitFor(() => {
        expect(result.current.allImages).toHaveLength(50);
      });

      rerender({ filters: [] });
      await waitFor(() => {
        expect(result.current.error).toBe(FILTER_FETCH_ERROR);
      });
      expect(result.current.allImages).toEqual([]);
      expect(result.current.displayedImages).toEqual([]);
      expect(result.current.hasMore).toBe(false);
    });

    it('retry runs the fetch for the same filters again and clears the error on success', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));
      fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockApiResponse) });
      const filters: ActiveFilters = [{ category: 'lib', values: ['matplotlib'] }];

      const { result } = renderHook(() => useFilterFetch({ activeFilters: filters }));
      await waitFor(() => {
        expect(result.current.error).toBe(FILTER_FETCH_ERROR);
      });

      act(() => result.current.retry());
      await waitFor(() => {
        expect(result.current.allImages).toHaveLength(50);
      });
      expect(result.current.error).toBe('');
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(fetchMock.mock.calls[1][0]).toBe(fetchMock.mock.calls[0][0]);
    });
  });
});
