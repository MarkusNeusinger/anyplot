import { describe, it, expect, vi } from 'vitest';
import {
  getCounts,
  getSelectedValuesForCategory,
  getAvailableValues,
  getAvailableValuesForGroup,
  getSearchResults,
} from './filters';
import type { FilterCounts, ActiveFilters } from '../types';

const mockFilterCounts: FilterCounts = {
  lib: { matplotlib: 10, seaborn: 8, plotly: 7, bokeh: 3 },
  spec: { 'scatter-basic': 5, 'heatmap-correlation': 4 },
  plot: { scatter: 8, heatmap: 4, bar: 6 },
  data: { tabular: 12, timeseries: 5 },
  dom: { science: 3 },
  feat: { legend: 7, colorbar: 4 },
  dep: {},
  tech: {},
  pat: {},
  prep: {},
  style: {},
};

describe('getAvailableValues', () => {
  it('returns all values sorted by count when no filters are active', () => {
    const result = getAvailableValues(mockFilterCounts, [], 'lib');

    expect(result).toEqual([
      ['matplotlib', 10],
      ['seaborn', 8],
      ['plotly', 7],
      ['bokeh', 3],
    ]);
  });

  it('excludes values that are already selected', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib', 'plotly'] },
    ];
    const result = getAvailableValues(mockFilterCounts, activeFilters, 'lib');

    expect(result).toEqual([
      ['seaborn', 8],
      ['bokeh', 3],
    ]);
  });

  it('excludes values selected across multiple groups of the same category', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
      { category: 'lib', values: ['seaborn'] },
    ];
    const result = getAvailableValues(mockFilterCounts, activeFilters, 'lib');

    expect(result).toEqual([
      ['plotly', 7],
      ['bokeh', 3],
    ]);
  });

  it('returns empty array when filterCounts is null', () => {
    const result = getAvailableValues(null, [], 'lib');
    expect(result).toEqual([]);
  });

  it('returns empty array for a category with no counts', () => {
    const result = getAvailableValues(mockFilterCounts, [], 'dep');
    expect(result).toEqual([]);
  });

  it('does not exclude values from other categories', () => {
    const activeFilters: ActiveFilters = [
      { category: 'plot', values: ['scatter'] },
    ];
    const result = getAvailableValues(mockFilterCounts, activeFilters, 'lib');

    // All lib values should still be available
    expect(result).toHaveLength(4);
    expect(result[0][0]).toBe('matplotlib');
  });

  it('returns empty array when all values are selected', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib', 'seaborn', 'plotly', 'bokeh'] },
    ];
    const result = getAvailableValues(mockFilterCounts, activeFilters, 'lib');
    expect(result).toEqual([]);
  });
});

describe('getAvailableValuesForGroup', () => {
  it('returns available values for a group with preview counts', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
    ];
    const orCounts = [{ seaborn: 5, plotly: 3 }];
    const currentTotal = 10;

    const result = getAvailableValuesForGroup(0, activeFilters, orCounts, currentTotal);

    // Values should be sorted by previewCount (currentTotal + count) descending
    expect(result).toEqual([
      ['seaborn', 15],
      ['plotly', 13],
    ]);
  });

  it('returns empty array for invalid group index', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
    ];
    const result = getAvailableValuesForGroup(5, activeFilters, [], 10);
    expect(result).toEqual([]);
  });

  it('excludes values already in the group', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib', 'seaborn'] },
    ];
    const orCounts = [{ matplotlib: 10, seaborn: 8, plotly: 3 }];
    const currentTotal = 10;

    const result = getAvailableValuesForGroup(0, activeFilters, orCounts, currentTotal);

    expect(result).toEqual([['plotly', 13]]);
  });

  it('returns empty array when orCounts for the group is empty', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
    ];
    const orCounts = [{}];
    const currentTotal = 10;

    const result = getAvailableValuesForGroup(0, activeFilters, orCounts, currentTotal);
    expect(result).toEqual([]);
  });

  it('handles missing orCounts entry gracefully', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
      { category: 'plot', values: ['scatter'] },
    ];
    // Only one entry in orCounts, so index 1 is missing
    const orCounts = [{ seaborn: 5 }];
    const currentTotal = 10;

    const result = getAvailableValuesForGroup(1, activeFilters, orCounts, currentTotal);
    expect(result).toEqual([]);
  });

  it('adds currentTotal to each count for preview', () => {
    const activeFilters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
    ];
    const orCounts = [{ plotly: 7 }];
    const currentTotal = 25;

    const result = getAvailableValuesForGroup(0, activeFilters, orCounts, currentTotal);
    expect(result).toEqual([['plotly', 32]]);
  });
});

describe('getSearchResults - additional coverage', () => {
  it('returns empty array for whitespace-only query', () => {
    const result = getSearchResults(mockFilterCounts, [], '   ', null);
    expect(result).toEqual([]);
  });

  it('searches across all categories when selectedCategory is null', () => {
    const result = getSearchResults(mockFilterCounts, [], 'scatter', null);
    const categories = new Set(result.map((r) => r.category));
    // Should find results in both spec and plot categories
    expect(categories.size).toBeGreaterThanOrEqual(1);
  });

  it('limits results to selectedCategory when provided', () => {
    const result = getSearchResults(mockFilterCounts, [], 'scatter', 'plot');
    result.forEach((r) => {
      expect(r.category).toBe('plot');
    });
  });

  it('skips categories with no items after excluding selected', () => {
    const activeFilters: ActiveFilters = [
      { category: 'dom', values: ['science'] },
    ];
    // 'dom' has only 'science' which is selected - should find no dom results
    const result = getSearchResults(mockFilterCounts, activeFilters, 'science', 'dom');
    expect(result).toEqual([]);
  });
});
