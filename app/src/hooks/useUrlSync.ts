/**
 * Hook for URL synchronization with filter state.
 *
 * Handles URL parsing and building.
 */

import { useLayoutEffect, useRef } from 'react';

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
 *
 * A layout effect: the layout records the navigation's pageview in its own
 * layout effect, which runs after this one, so a visit that restores the
 * remembered filters is one pageview, of the filtered page. That first run
 * therefore records nothing itself. From then on a filter change is a page of
 * its own, and no navigation tells the layout about it.
 */
export function useUrlSync({ activeFilters, onTrackPageview }: UseUrlSyncOptions): void {
  const synced = useRef(false);

  useLayoutEffect(() => {
    const newUrl = buildFilterUrl(activeFilters);
    window.history.replaceState({}, '', newUrl);

    if (synced.current) onTrackPageview();
    synced.current = true;
  }, [activeFilters, onTrackPageview]);
}
