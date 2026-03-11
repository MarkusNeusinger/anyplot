/**
 * Hook for managing filter state and URL synchronization.
 *
 * Uses persistent state from Layout context to survive navigation.
 * Composes useUrlSync and useFilterFetch for cleaner separation of concerns.
 */

import { useState, useCallback, useEffect, useRef } from 'react';

import type { PlotImage, FilterCategory, ActiveFilters, FilterCounts } from '../types';
import { FILTER_CATEGORIES } from '../types';
import { useHomeState } from './useLayoutContext';
import { parseUrlFilters, useUrlSync } from './useUrlSync';
import { useFilterFetch } from './useFilterFetch';

/**
 * Check if filters are empty.
 */
export function isFiltersEmpty(filters: ActiveFilters): boolean {
  return filters.length === 0 || filters.every((f) => f.values.length === 0);
}

interface UseFilterStateOptions {
  onTrackPageview: () => void;
  onTrackEvent: (event: string, props?: Record<string, string>) => void;
}

interface UseFilterStateReturn {
  // State
  activeFilters: ActiveFilters;
  filterCounts: FilterCounts | null;
  globalCounts: FilterCounts | null;
  orCounts: Record<string, number>[];
  specTitles: Record<string, string>;
  allImages: PlotImage[];
  displayedImages: PlotImage[];
  hasMore: boolean;
  loading: boolean;
  error: string;

  // Setters for external state
  setDisplayedImages: React.Dispatch<React.SetStateAction<PlotImage[]>>;
  setHasMore: React.Dispatch<React.SetStateAction<boolean>>;
  setError: React.Dispatch<React.SetStateAction<string>>;

  // Callbacks
  handleAddFilter: (category: FilterCategory, value: string) => void;
  handleAddValueToGroup: (groupIndex: number, value: string) => void;
  handleRemoveFilter: (groupIndex: number, value: string) => void;
  handleRemoveGroup: (groupIndex: number) => void;
  handleRandom: (method?: 'click' | 'space' | 'doubletap') => void;

  // Animation state for random
  randomAnimation: { index: number; phase: 'out' | 'in'; oldLabel?: string } | null;
}

export function useFilterState({
  onTrackPageview,
  onTrackEvent,
}: UseFilterStateOptions): UseFilterStateReturn {
  const { homeStateRef, setHomeState } = useHomeState();

  // Initialize from persistent state (ref) or URL params
  const [activeFilters, setActiveFilters] = useState<ActiveFilters>(() =>
    homeStateRef.current.initialized ? homeStateRef.current.activeFilters : parseUrlFilters()
  );

  const [randomAnimation, setRandomAnimation] = useState<{
    index: number;
    phase: 'out' | 'in';
    oldLabel?: string;
  } | null>(null);

  // Refs for stable callbacks
  const activeFiltersRef = useRef(activeFilters);
  activeFiltersRef.current = activeFilters;

  // Check if we should skip initial fetch (restored from persistent state with same filters)
  const shouldSkipInitialFetch =
    homeStateRef.current.initialized &&
    JSON.stringify(homeStateRef.current.activeFilters) === JSON.stringify(activeFilters);

  // Use extracted hooks
  useUrlSync({ activeFilters, onTrackPageview });

  const {
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
  } = useFilterFetch({
    activeFilters,
    initialState: homeStateRef.current.initialized
      ? {
          filterCounts: homeStateRef.current.filterCounts,
          globalCounts: homeStateRef.current.globalCounts,
          orCounts: homeStateRef.current.orCounts,
          allImages: homeStateRef.current.allImages,
          displayedImages: homeStateRef.current.displayedImages,
          hasMore: homeStateRef.current.hasMore,
        }
      : undefined,
    skipInitialFetch: shouldSkipInitialFetch,
  });

  // Sync state changes back to persistent context
  useEffect(() => {
    if (allImages.length > 0 || displayedImages.length > 0) {
      setHomeState((prev) => ({
        ...prev,
        allImages,
        displayedImages,
        activeFilters,
        filterCounts,
        globalCounts,
        orCounts,
        hasMore,
        initialized: true,
      }));
    }
  }, [allImages, displayedImages, activeFilters, filterCounts, globalCounts, orCounts, hasMore, setHomeState]);

  // Add a new filter group (creates new chip - AND with other groups)
  const handleAddFilter = useCallback((category: FilterCategory, value: string) => {
    setActiveFilters((prev) => [...prev, { category, values: [value] }]);
  }, []);

  // Add value to existing group by index (OR within that group)
  const handleAddValueToGroup = useCallback((groupIndex: number, value: string) => {
    setActiveFilters((prev) => {
      const newFilters = [...prev];
      const group = newFilters[groupIndex];
      if (group && !group.values.includes(value)) {
        newFilters[groupIndex] = { ...group, values: [...group.values, value] };
      }
      return newFilters;
    });
  }, []);

  // Remove a filter value from a specific group
  const handleRemoveFilter = useCallback(
    (groupIndex: number, value: string) => {
      const group = activeFiltersRef.current[groupIndex];
      if (group) {
        onTrackEvent('filter_remove', { category: group.category, value });
      }
      setActiveFilters((prev) => {
        const newFilters = [...prev];
        const grp = newFilters[groupIndex];
        if (!grp) return prev;

        const updatedValues = grp.values.filter((v) => v !== value);
        if (updatedValues.length === 0) {
          return newFilters.filter((_, i) => i !== groupIndex);
        }
        newFilters[groupIndex] = { ...grp, values: updatedValues };
        return newFilters;
      });
    },
    [onTrackEvent]
  );

  // Remove entire group by index
  const handleRemoveGroup = useCallback(
    (groupIndex: number) => {
      const group = activeFiltersRef.current[groupIndex];
      if (group) {
        onTrackEvent('filter_remove', { category: group.category, value: group.values.join(',') });
      }
      setActiveFilters((prev) => prev.filter((_, i) => i !== groupIndex));
    },
    [onTrackEvent]
  );

  // Random filter - replaces last filter slot (or adds first one)
  const handleRandom = useCallback(
    (method: 'click' | 'space' | 'doubletap' = 'click') => {
      const currentFilters = activeFiltersRef.current;
      // Use contextual counts if filters exist, otherwise global
      const countsToUse = currentFilters.length > 0 ? filterCounts : globalCounts;
      if (!countsToUse) return;

      const availableCategories = FILTER_CATEGORIES.filter((cat) => {
        const counts = countsToUse[cat];
        return counts && Object.keys(counts).length > 0;
      });

      if (availableCategories.length === 0) return;

      const randomCategory = availableCategories[Math.floor(Math.random() * availableCategories.length)];
      const values = Object.keys(countsToUse[randomCategory]);

      if (values.length === 0) return;

      const randomValue = values[Math.floor(Math.random() * values.length)];
      const newFilter = { category: randomCategory, values: [randomValue] };

      // Get old label before changing
      const newIndex = currentFilters.length === 0 ? 0 : currentFilters.length - 1;
      const oldGroup = currentFilters[newIndex];
      const oldLabel = oldGroup ? `${oldGroup.category}:${oldGroup.values.join(',')}` : '';

      // Start animation with old label, change filter immediately (so images load)
      setRandomAnimation({ index: newIndex, phase: 'out', oldLabel });
      setActiveFilters((prev) => {
        if (prev.length === 0) {
          return [newFilter];
        }
        return [...prev.slice(0, -1), newFilter];
      });

      // Switch to 'in' phase at halfway point
      setTimeout(() => {
        setRandomAnimation({ index: newIndex, phase: 'in' });
      }, 500);

      // Clear animation state
      setTimeout(() => setRandomAnimation(null), 1000);

      onTrackEvent('random_filter', { category: randomCategory, value: randomValue, method });
    },
    [filterCounts, globalCounts, onTrackEvent]
  );

  return {
    // State
    activeFilters,
    filterCounts,
    globalCounts,
    orCounts,
    specTitles,
    allImages,
    displayedImages,
    hasMore,
    loading,
    error,

    // Setters
    setDisplayedImages,
    setHasMore,
    setError,

    // Callbacks
    handleAddFilter,
    handleAddValueToGroup,
    handleRemoveFilter,
    handleRemoveGroup,
    handleRandom,

    // Animation
    randomAnimation,
  };
}
