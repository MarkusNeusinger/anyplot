/**
 * Hook for fetching filtered plot images.
 *
 * Handles API calls, image shuffling, and pagination state.
 */

import { useState, useEffect, useMemo, useRef } from 'react';

import type { PlotImage, ActiveFilters, FilterCounts } from '../types';
import { API_URL, BATCH_SIZE } from '../constants';
import { shuffleArray } from '../utils/shuffle';

interface FilterFetchState {
  filterCounts: FilterCounts | null;
  globalCounts: FilterCounts | null;
  orCounts: Record<string, number>[];
  specTitles: Record<string, string>;
  allImages: PlotImage[];
  displayedImages: PlotImage[];
  hasMore: boolean;
  loading: boolean;
  error: string;
}

interface UseFilterFetchOptions {
  activeFilters: ActiveFilters;
  initialState?: Partial<FilterFetchState>;
  skipInitialFetch?: boolean;
}

interface UseFilterFetchReturn extends FilterFetchState {
  setDisplayedImages: React.Dispatch<React.SetStateAction<PlotImage[]>>;
  setHasMore: React.Dispatch<React.SetStateAction<boolean>>;
  setError: React.Dispatch<React.SetStateAction<string>>;
}

/**
 * Hook to fetch filtered images and manage related state.
 */
export function useFilterFetch({
  activeFilters,
  initialState = {},
  skipInitialFetch = false,
}: UseFilterFetchOptions): UseFilterFetchReturn {
  const [filterCounts, setFilterCounts] = useState<FilterCounts | null>(initialState.filterCounts ?? null);
  const [globalCounts, setGlobalCounts] = useState<FilterCounts | null>(initialState.globalCounts ?? null);
  const [orCounts, setOrCounts] = useState<Record<string, number>[]>(initialState.orCounts ?? []);
  const [specTitles, setSpecTitles] = useState<Record<string, string>>(initialState.specTitles ?? {});
  const [allImages, setAllImages] = useState<PlotImage[]>(initialState.allImages ?? []);
  const [displayedImages, setDisplayedImages] = useState<PlotImage[]>(initialState.displayedImages ?? []);
  const [hasMore, setHasMore] = useState(initialState.hasMore ?? false);
  const [loading, setLoading] = useState(!skipInitialFetch);
  const [error, setError] = useState<string>('');

  // Track if we should skip initial fetch
  const skipRef = useRef(skipInitialFetch);
  const initialFiltersRef = useRef(JSON.stringify(activeFilters));

  // Stringify the filters so the effect reruns when CONTENTS change, not when
  // the parent happens to re-render and hand us a fresh array reference.
  // Without this memo every parent render re-fired the fetch even when the
  // filter contents were identical.
  const filtersKey = useMemo(() => JSON.stringify(activeFilters), [activeFilters]);

  useEffect(() => {
    // Skip fetch on first mount if requested and filters match
    if (skipRef.current && filtersKey === initialFiltersRef.current) {
      skipRef.current = false;
      return;
    }
    skipRef.current = false;

    const abortController = new AbortController();

    const fetchFilteredImages = async () => {
      setLoading(true);

      try {
        // Parse from the stable string key so the effect doesn't depend on
        // `activeFilters` directly (whose reference changes per render).
        const filters: ActiveFilters = JSON.parse(filtersKey);

        // Build query string from filters
        const params = new URLSearchParams();
        filters.forEach(({ category, values }) => {
          if (values.length > 0) {
            params.append(category, values.join(','));
          }
        });

        const queryString = params.toString();
        const url = `${API_URL}/plots/filter${queryString ? `?${queryString}` : ''}`;

        const response = await fetch(url, { signal: abortController.signal });
        if (!response.ok) throw new Error('Failed to fetch filtered plots');

        const data = await response.json();

        if (abortController.signal.aborted) return;

        // Update filter counts and spec titles
        setFilterCounts(data.counts);
        setGlobalCounts(data.globalCounts || data.counts);
        setOrCounts(data.orCounts || []);
        setSpecTitles(data.specTitles || {});

        // Shuffle images randomly on each load
        const shuffled = shuffleArray<PlotImage>(data.images || []);
        setAllImages(shuffled);

        // Initial display count
        setDisplayedImages(shuffled.slice(0, BATCH_SIZE));
        setHasMore(shuffled.length > BATCH_SIZE);
      } catch (err) {
        if (abortController.signal.aborted) return;
        setError(`Error loading images: ${err}`);
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchFilteredImages();

    return () => abortController.abort();
  }, [filtersKey]);

  return {
    filterCounts,
    globalCounts,
    orCounts,
    specTitles,
    allImages,
    displayedImages,
    hasMore,
    loading,
    error,
    setDisplayedImages,
    setHasMore,
    setError,
  };
}
