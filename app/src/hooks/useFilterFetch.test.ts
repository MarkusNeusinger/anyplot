import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useFilterFetch } from './useFilterFetch';
import type { ActiveFilters, PlotImage } from '../types';

describe('useFilterFetch', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    globalThis.fetch = fetchMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockImages: PlotImage[] = Array.from({ length: 50 }, (_, i) => ({
    library: 'matplotlib',
    url: `https://example.com/img${i}.png`,
    spec_id: `spec-${i}`,
  }));

  const mockApiResponse = {
    images: mockImages,
    counts: { lib: { matplotlib: 50 }, spec: {}, plot: {}, data: {}, dom: {}, feat: {}, dep: {}, tech: {}, pat: {}, prep: {}, style: {} },
    globalCounts: { lib: { matplotlib: 50 }, spec: {}, plot: {}, data: {}, dom: {}, feat: {}, dep: {}, tech: {}, pat: {}, prep: {}, style: {} },
    orCounts: [],
    specTitles: { 'spec-0': 'Scatter Plot' },
  };

  describe('initial state', () => {
    it('starts loading when no initialState provided', () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      const { result } = renderHook(() =>
        useFilterFetch({ activeFilters: [] })
      );
      expect(result.current.loading).toBe(true);
    });

    it('uses provided initial state and skips fetch', () => {
      const initialImages: PlotImage[] = [{ library: 'seaborn', url: 'test.png' }];

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

      const { result } = renderHook(() =>
        useFilterFetch({ activeFilters: [] })
      );

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

      const { result } = renderHook(() =>
        useFilterFetch({ activeFilters: [] })
      );

      await waitFor(() => {
        expect(result.current.displayedImages).toHaveLength(5);
      });

      expect(result.current.hasMore).toBe(false);
    });

    it('stores filter counts and spec titles', async () => {
      fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockApiResponse) });

      const { result } = renderHook(() =>
        useFilterFetch({ activeFilters: [] })
      );

      await waitFor(() => {
        expect(result.current.filterCounts).not.toBeNull();
      });

      expect(result.current.filterCounts).toEqual(mockApiResponse.counts);
      expect(result.current.specTitles).toEqual({ 'spec-0': 'Scatter Plot' });
    });
  });

  describe('error handling', () => {
    it('sets error on network failure', async () => {
      fetchMock.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() =>
        useFilterFetch({ activeFilters: [] })
      );

      await waitFor(() => {
        expect(result.current.error).toContain('Error loading images');
      });
    });

    it('sets error on non-ok HTTP response', async () => {
      fetchMock.mockResolvedValue({ ok: false });

      const { result } = renderHook(() =>
        useFilterFetch({ activeFilters: [] })
      );

      await waitFor(() => {
        expect(result.current.error).toContain('Error loading images');
      });
    });
  });
});
