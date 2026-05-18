import { describe, it, expect } from 'vitest';
import { getSearchResults } from './filters';
import type { FilterCounts, ActiveFilters } from '../types';

describe('getSearchResults', () => {
  const mockFilterCounts: FilterCounts = {
    lang: { python: 25, r: 0 },
    spec: {
      'scatter-basic': 5,
      'scatter-color-mapped': 3,
      'heatmap-correlation': 4,
      'histogram-kde': 2,
      'bar-grouped': 6,
    },
    lib: {
      matplotlib: 10,
      seaborn: 8,
      plotly: 7,
    },
    plot: { scatter: 8, heatmap: 4, histogram: 2, bar: 6 },
    data: {},
    dom: {},
    feat: { basic: 15, advanced: 10 },
    dep: {},
    tech: {},
    pat: {},
    prep: {},
    style: {},
  };

  const emptyFilters: ActiveFilters = [];

  it('returns empty array when filterCounts is null', () => {
    const results = getSearchResults(null, emptyFilters, 'scatter', null);
    expect(results).toEqual([]);
  });

  it('returns empty array when searchQuery is empty', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, '', null);
    expect(results).toEqual([]);
  });

  it('finds exact matches', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', null);

    expect(results.length).toBeGreaterThan(0);
    expect(results.some((r) => r.value === 'scatter-basic')).toBe(true);
  });

  it('finds matches with typos', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scater', null);

    expect(results.length).toBeGreaterThan(0);
    expect(results.some((r) => r.value.includes('scatter'))).toBe(true);
  });

  it('assigns matchType correctly', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', null);

    expect(results.length).toBeGreaterThan(0);
    results.forEach((result) => {
      expect(['exact', 'fuzzy']).toContain(result.matchType);
    });
  });

  it('sorts exact matches before fuzzy matches', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scater', null);

    if (results.length > 1) {
      const exactIndices = results
        .map((r, i) => (r.matchType === 'exact' ? i : -1))
        .filter((i) => i >= 0);
      const fuzzyIndices = results
        .map((r, i) => (r.matchType === 'fuzzy' ? i : -1))
        .filter((i) => i >= 0);

      if (exactIndices.length > 0 && fuzzyIndices.length > 0) {
        const maxExactIndex = Math.max(...exactIndices);
        const minFuzzyIndex = Math.min(...fuzzyIndices);
        expect(maxExactIndex).toBeLessThan(minFuzzyIndex);
      }
    }
  });

  it('filters by selected category', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', 'spec');

    results.forEach((result) => {
      expect(result.category).toBe('spec');
    });
  });

  it('excludes already selected values', () => {
    const activeFilters: ActiveFilters = [{ category: 'spec', values: ['scatter-basic'] }];
    const results = getSearchResults(mockFilterCounts, activeFilters, 'scatter', null);

    expect(results.some((r) => r.value === 'scatter-basic')).toBe(false);
  });

  it('searches spec titles when provided', () => {
    const specTitles = {
      'scatter-basic': 'Basic Scatter Plot',
      'heatmap-correlation': 'Correlation Heatmap Matrix',
    };
    const results = getSearchResults(
      mockFilterCounts,
      emptyFilters,
      'correlation matrix',
      'spec',
      specTitles
    );

    expect(results.length).toBeGreaterThan(0);
    expect(results.some((r) => r.value === 'heatmap-correlation')).toBe(true);
  });

  it('includes count in results', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', null);

    expect(results.length).toBeGreaterThan(0);
    results.forEach((result) => {
      expect(typeof result.count).toBe('number');
      expect(result.count).toBeGreaterThan(0);
    });
  });

  it('supports multi-word queries', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'hi k', 'spec');

    expect(results.some((r) => r.value === 'histogram-kde')).toBe(true);
  });
});
