/**
 * Filter utility functions for FilterBar component.
 *
 * Pure functions extracted for reusability and testing.
 */

import type { ActiveFilters, FilterCategory, FilterCounts, PlotImage } from 'src/types';
import { FILTER_CATEGORIES } from 'src/types';
import { createFuzzySearcher, getMatchType, type MatchType } from 'src/utils/fuzzySearch';

/**
 * Words that name "a chart" or only join two terms ("and", "with", "of"), in
 * English and in the languages the agent chat answers in
 * (agents/anyplot/prompts/refusals.yaml: de, fr, es, it, pt, nl, pl). Stored
 * folded: lowercase, without diacritics.
 *
 * They carry no meaning for the search but break it: Fuse's extended search
 * treats a space as AND and needs every word inside ONE field, so "line chart"
 * misses the spec titled "Basic Line Plot", "bar chart" ranks the title that
 * starts with "Bar Chart" above `plot:bar`, and the "de" of "gráfico de violin"
 * matches no field at all. One-letter joiners (Spanish "y", Polish "i" and "z",
 * Italian and Portuguese "e") are left out because axis names and "z score"
 * use them.
 */
const GENERIC_QUERY_WORDS: ReadonlySet<string> = new Set([
  // en
  'chart',
  'charts',
  'plot',
  'plots',
  'graph',
  'graphs',
  'diagram',
  'diagrams',
  'and',
  'with',
  'of',
  // de
  'diagramm',
  'diagramme',
  'grafik',
  'grafiken',
  'und',
  'mit',
  'von',
  // fr
  'graphique',
  'graphiques',
  'graphe',
  'graphes',
  'diagrammes',
  'et',
  'avec',
  'de',
  'du',
  'des',
  // es, pt
  'grafico',
  'graficos',
  'grafica',
  'graficas',
  'diagrama',
  'diagramas',
  'con',
  'com',
  'del',
  'da',
  'do',
  // it
  'grafici',
  'diagramma',
  'diagrammi',
  'di',
  // nl
  'grafiek',
  'grafieken',
  'diagrammen',
  'en',
  'met',
  'van',
  // pl
  'wykres',
  'wykresy',
  'wykresu',
  'wykresow',
]);

/**
 * Lowercase, drop diacritics the way Fuse's `ignoreDiacritics` compares, and
 * drop sentence punctuation at the end ("plot," in "scatter plot, line").
 * Leading characters stay: `!`, `^`, `=` and `'` are Fuse operators, and
 * "!chart" must keep meaning "without chart".
 */
function foldWord(word: string): string {
  return word
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/ß/g, 'ss')
    .replace(/[,;:.?!]+$/, '');
}

/**
 * Prepare a raw search box query for the fuzzy search: lowercase, trim,
 * collapse whitespace, and drop the generic words above. When the query holds
 * nothing but generic words ("plot", "chart and graph"), the raw query is kept,
 * so those words still find what they name (`lib:plotly`, `lib:chartjs`).
 */
export function normalizeSearchQuery(searchQuery: string): string {
  const words = searchQuery.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const meaningful = words.filter(word => !GENERIC_QUERY_WORDS.has(foldWord(word)));
  return (meaningful.length > 0 ? meaningful : words).join(' ');
}

/** Number of distinct specs among the gallery's images (one image is one spec in one library). */
export function countDistinctSpecs(images: readonly PlotImage[]): number {
  return new Set(images.map(image => image.spec_id).filter(Boolean)).size;
}

/** The gallery counter's totals with their units, for example "8 specs · 120 plots". */
export function formatGalleryTotals(specCount: number, plotCount: number): string {
  const specs = `${specCount} ${specCount === 1 ? 'spec' : 'specs'}`;
  const plots = `${plotCount} ${plotCount === 1 ? 'plot' : 'plots'}`;
  return `${specs} · ${plots}`;
}

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
 * For the "spec" category, also searches through spec titles. The query goes
 * through `normalizeSearchQuery` first.
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

  const query = normalizeSearchQuery(searchQuery);
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
