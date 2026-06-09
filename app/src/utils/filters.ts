/**
 * Filter utility functions for FilterBar component.
 *
 * Pure functions extracted for reusability and testing.
 */

import type { ActiveFilters, FilterCategory, FilterCounts } from 'src/types';
import { FILTER_CATEGORIES } from 'src/types';
import { createFuzzySearcher, getMatchType, type MatchType } from 'src/utils/fuzzySearch';

/**
 * Get counts for a specific filter category.
 */
export function getCounts(
  filterCounts: FilterCounts | null,
  category: FilterCategory
): Record<string, number> {
  return filterCounts?.[category] || {};
}

/**
 * Get all selected values across all groups for a category.
 */
export function getSelectedValuesForCategory(
  activeFilters: ActiveFilters,
  category: FilterCategory
): string[] {
  return activeFilters.filter(f => f.category === category).flatMap(f => f.values);
}

/**
 * Get available values for a category (not already selected in any group).
 *
 * @returns Array of [value, count] tuples sorted by count descending
 */
export function getAvailableValues(
  filterCounts: FilterCounts | null,
  activeFilters: ActiveFilters,
  category: FilterCategory
): [string, number][] {
  const counts = getCounts(filterCounts, category);
  const selected = getSelectedValuesForCategory(activeFilters, category);

  return Object.entries(counts)
    .filter(([value]) => !selected.includes(value))
    .sort((a, b) => b[1] - a[1]);
}

/**
 * Get available values for adding to a specific group (OR operation).
 * Uses orCounts which has counts with all OTHER filters applied.
 *
 * @param groupIndex - Index of the filter group
 * @param activeFilters - Current active filters
 * @param orCounts - Per-group OR counts from API
 * @param currentTotal - Current total number of images
 * @returns Array of [value, previewCount] tuples
 */
export function getAvailableValuesForGroup(
  groupIndex: number,
  activeFilters: ActiveFilters,
  orCounts: Record<string, number>[],
  currentTotal: number
): [string, number][] {
  const group = activeFilters[groupIndex];
  if (!group) return [];

  const groupOrCounts = orCounts[groupIndex] || {};

  return Object.entries(groupOrCounts)
    .filter(([value]) => !group.values.includes(value))
    .map(([value, count]) => [value, currentTotal + count] as [string, number])
    .sort((a, b) => b[1] - a[1]);
}

export interface SearchResult {
  category: FilterCategory;
  value: string;
  count: number;
  matchType: MatchType;
}

/**
 * Search across all filter categories using fuzzy matching.
 *
 * Uses fuse.js for typo-tolerant search. Results are grouped by match quality:
 * - 'exact': Very close matches (score < 0.1)
 * - 'fuzzy': Looser matches with typo tolerance (score >= 0.1)
 *
 * For the "spec" category, also searches through spec titles.
 *
 * @param filterCounts - Available filter counts
 * @param activeFilters - Current active filters
 * @param searchQuery - Search query string
 * @param selectedCategory - Optional category to limit search to
 * @param specTitles - Optional mapping of spec_id to title for enhanced spec search
 * @returns Matching results sorted by match quality and count
 *
 * @example
 * // Query: "scater" will find "scatter-basic" (typo tolerance)
 * // Query: "heatmp" will find "heatmap-correlation"
 * // Exact matches appear first, fuzzy matches after a divider
 */
export function getSearchResults(
  filterCounts: FilterCounts | null,
  activeFilters: ActiveFilters,
  searchQuery: string,
  selectedCategory: FilterCategory | null,
  specTitles: Record<string, string> = {}
): SearchResult[] {
  if (!filterCounts || !searchQuery.trim()) return [];

  const query = searchQuery.toLowerCase().trim();
  const results: Array<SearchResult & { score: number }> = [];

  const categoriesToSearch = selectedCategory ? [selectedCategory] : FILTER_CATEGORIES;

  for (const category of categoriesToSearch) {
    const counts = getCounts(filterCounts, category);
    const selected = getSelectedValuesForCategory(activeFilters, category);

    // Build searchable items for this category
    const items = Object.keys(counts)
      .filter(value => !selected.includes(value))
      .map(value => ({
        value,
        title: category === 'spec' ? specTitles[value] : undefined,
        count: counts[value],
      }));

    if (items.length === 0) continue;

    // Create fuzzy searcher and search
    const searcher = createFuzzySearcher(items);
    const matches = searcher.search(query);

    for (const match of matches) {
      const score = match.score ?? 0;
      results.push({
        category,
        value: match.item.value,
        count: match.item.count,
        score,
        matchType: getMatchType(score),
      });
    }
  }

  // Sort: exact first, then by score (lower = better), then by count
  return results.sort((a, b) => {
    // Exact matches before fuzzy
    if (a.matchType !== b.matchType) {
      return a.matchType === 'exact' ? -1 : 1;
    }
    // Within same type, sort by score (lower is better in fuse.js)
    if (a.score !== b.score) {
      return a.score - b.score;
    }
    // Then by count (higher is better)
    return b.count - a.count;
  });
}
