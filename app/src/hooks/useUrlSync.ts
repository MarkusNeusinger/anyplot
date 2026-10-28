/**
 * Hook for URL synchronization with filter state.
 *
 * Handles URL parsing, and building.
 */

import { useEffect } from 'react';

import type { ActiveFilters } from 'src/types';
import { FILTER_CATEGORIES } from 'src/types';

/**
 * Parse URL params into ActiveFilters.
 * URL format: ?lib=matplotlib&lib=seaborn (AND) or ?lib=matplotlib,seaborn (OR within group)
 */
export function parseUrlFilters(): ActiveFilters {
  const params = new URLSearchParams(window.location.search);
  const filters: ActiveFilters = [];

  FILTER_CATEGORIES.forEach(category => {
    const allValues = params.getAll(category);
    allValues.forEach(value => {
      if (value) {
        const values = value
          .split(',')
          .map(v => v.trim())
          .filter(Boolean);
        if (values.length > 0) {
          filters.push({ category, values });
        }
      }
    });
  });

  return filters;
}

/**
 * Build URL from ActiveFilters.
 */
export function buildFilterUrl(filters: ActiveFilters): string {
  const params = new URLSearchParams();
  filters.forEach(({ category, values }) => {
    if (values.length > 0) {
      params.append(category, values.join(','));
    }
  });
  const queryString = params.toString();
  const basePath = window.location.pathname;
  return queryString ? `${basePath}?${queryString}` : basePath;
}

interface UseUrlSyncOptions {
  activeFilters: ActiveFilters;
  onTrackPageview: () => void;
}

/**
 * Hook to synchronize active filters with URL.
 */
export function useUrlSync({ activeFilters, onTrackPageview }: UseUrlSyncOptions): void {
  useEffect(() => {
    const newUrl = buildFilterUrl(activeFilters);
    window.history.replaceState({}, '', newUrl);

    onTrackPageview();
  }, [activeFilters, onTrackPageview]);
}
