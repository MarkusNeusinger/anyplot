/**
 * Fuzzy search utilities using fuse.js.
 *
 * Provides typo-tolerant search for filter values.
 */

import Fuse from 'fuse.js';

/** Maximum score to count as a match (0 = perfect, 1 = no match) */
const FUZZY_THRESHOLD = 0.3;

/** Score below this is considered an "exact" match for UI grouping */
const EXACT_THRESHOLD = 0.1;

export type MatchType = 'exact' | 'fuzzy';

export interface SearchableItem {
  value: string;
  title?: string;
}

export interface FuzzyResult<T extends SearchableItem> {
  item: T;
  score: number;
  matchType: MatchType;
}

/**
 * Create a fuzzy searcher for filter values.
 *
 * @param items - Items to search through
 * @returns Configured Fuse instance
 */
export function createFuzzySearcher<T extends SearchableItem>(items: T[]): Fuse<T> {
  return new Fuse(items, {
    keys: ['value', 'title'],
    threshold: FUZZY_THRESHOLD,
    distance: 100,
    minMatchCharLength: 1,
    includeScore: true,
    useExtendedSearch: true,
  });
}

/**
 * Determine match type based on fuse.js score.
 *
 * @param score - Fuse.js score (0 = perfect match, 1 = no match)
 * @returns 'exact' for very good matches, 'fuzzy' for looser matches
 */
export function getMatchType(score: number): MatchType {
  return score < EXACT_THRESHOLD ? 'exact' : 'fuzzy';
}

/**
 * Perform fuzzy search and return results with match type.
 *
 * @param searcher - Fuse instance
 * @param query - Search query
 * @returns Array of results with score and match type
 */
export function fuzzySearch<T extends SearchableItem>(
  searcher: Fuse<T>,
  query: string
): FuzzyResult<T>[] {
  const results = searcher.search(query);

  return results.map(result => ({
    item: result.item,
    score: result.score ?? 0,
    matchType: getMatchType(result.score ?? 0),
  }));
}
