import { describe, expect, it } from 'vitest';

import type { ActiveFilters, FilterCounts, PlotImage } from 'src/types';
import {
  countDistinctSpecs,
  formatGalleryTotals,
  getSearchResults,
  normalizeSearchQuery,
} from 'src/utils/filters';

describe('normalizeSearchQuery', () => {
  it('drops generic English nouns and joiners', () => {
    expect(normalizeSearchQuery('bar chart')).toBe('bar');
    expect(normalizeSearchQuery('Line Plot')).toBe('line');
    expect(normalizeSearchQuery('network graph')).toBe('network');
    expect(normalizeSearchQuery('bar chart with error bars')).toBe('bar error bars');
    expect(normalizeSearchQuery('black and white')).toBe('black white');
  });

  it('drops the same words in the languages of the agent chat', () => {
    expect(normalizeSearchQuery('Sankey Diagramm')).toBe('sankey');
    expect(normalizeSearchQuery('scatter und regression')).toBe('scatter regression');
    expect(normalizeSearchQuery('graphique radar')).toBe('radar');
    expect(normalizeSearchQuery('gráfico de violin')).toBe('violin');
    expect(normalizeSearchQuery('diagrammes de dispersion')).toBe('dispersion');
    expect(normalizeSearchQuery('diagramma di treemap')).toBe('treemap');
    expect(normalizeSearchQuery('grafiek van heatmap')).toBe('heatmap');
    expect(normalizeSearchQuery('wykresów pie')).toBe('pie');
    expect(normalizeSearchQuery('distribution of income')).toBe('distribution income');
  });

  it('drops a generic word with sentence punctuation after it', () => {
    expect(normalizeSearchQuery('scatter plot, line')).toBe('scatter line');
    expect(normalizeSearchQuery('bar chart.')).toBe('bar');
    expect(normalizeSearchQuery('pie chart!')).toBe('pie');
  });

  it('leaves Fuse operators and the words they carry alone', () => {
    expect(normalizeSearchQuery('bar !chart')).toBe('bar !chart');
    expect(normalizeSearchQuery("'plot =chart ^graph")).toBe("'plot =chart ^graph");
    expect(normalizeSearchQuery('chart.js')).toBe('chart.js');
  });

  it('compares generic words without diacritics but keeps the other words as typed', () => {
    expect(normalizeSearchQuery('GRÁFICO säulen')).toBe('säulen');
  });

  it('falls back to the raw query when only generic words are left', () => {
    expect(normalizeSearchQuery('plot')).toBe('plot');
    expect(normalizeSearchQuery('  Chart  and   Graph ')).toBe('chart and graph');
  });

  it('keeps words that only contain a generic word', () => {
    expect(normalizeSearchQuery('plotly chart')).toBe('plotly');
    expect(normalizeSearchQuery('chartjs')).toBe('chartjs');
    expect(normalizeSearchQuery('bar-chart')).toBe('bar-chart');
  });

  it('keeps one-letter words, which name axes', () => {
    expect(normalizeSearchQuery('z score')).toBe('z score');
    expect(normalizeSearchQuery('x y scatter')).toBe('x y scatter');
  });

  it('lowercases, trims and collapses whitespace', () => {
    expect(normalizeSearchQuery('  Heat   Map ')).toBe('heat map');
    expect(normalizeSearchQuery('   ')).toBe('');
  });
});

describe('countDistinctSpecs', () => {
  const image = (spec_id: string | undefined, library: string): PlotImage => ({
    spec_id,
    library,
    language: 'python',
    url: `https://example.com/${spec_id}-${library}.png`,
  });

  it('counts each spec once across its libraries', () => {
    const images = [
      image('bar-basic', 'matplotlib'),
      image('bar-basic', 'seaborn'),
      image('pie-basic', 'plotly'),
    ];
    expect(countDistinctSpecs(images)).toBe(2);
  });

  it('skips images without a spec_id and handles an empty list', () => {
    expect(countDistinctSpecs([image(undefined, 'bokeh'), image('pie-basic', 'bokeh')])).toBe(1);
    expect(countDistinctSpecs([])).toBe(0);
  });
});

describe('formatGalleryTotals', () => {
  it('names both units', () => {
    expect(formatGalleryTotals(8, 120)).toBe('8 specs · 120 plots');
  });

  it('uses the singular for one', () => {
    expect(formatGalleryTotals(1, 1)).toBe('1 spec · 1 plot');
    expect(formatGalleryTotals(1, 15)).toBe('1 spec · 15 plots');
  });
});

describe('getSearchResults with generic words and titles', () => {
  const counts: FilterCounts = {
    lang: { python: 40 },
    lib: { matplotlib: 20, chartjs: 20 },
    spec: { 'bar-error': 15, 'bar-basic': 15, 'line-basic': 15, 'bar-pareto': 15 },
    plot: { bar: 45, line: 15 },
    data: {},
    dom: {},
    feat: {},
    dep: {},
    tech: {},
    pat: {},
    prep: {},
    style: {},
  };
  const titles = {
    'bar-error': 'Bar Chart with Error Bars',
    'bar-basic': 'Basic Bar Chart',
    'line-basic': 'Basic Line Plot',
    'bar-pareto': 'Pareto Chart with Cumulative Line',
  };

  it('ranks the plot type first for "bar chart"', () => {
    const results = getSearchResults(counts, [], 'bar chart', null, titles);
    expect(results[0]).toMatchObject({ category: 'plot', value: 'bar' });
  });

  it('finds the line spec for "line chart", whose title says "Plot"', () => {
    const results = getSearchResults(counts, [], 'line chart', null, titles);
    expect(results[0]).toMatchObject({ category: 'plot', value: 'line' });
    expect(results.some(r => r.value === 'line-basic')).toBe(true);
  });

  it('still finds a library named after a generic word', () => {
    const results = getSearchResults(counts, [], 'chart', 'lib', titles);
    expect(results.map(r => r.value)).toContain('chartjs');
  });
});

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
    expect(results.some(r => r.value === 'scatter-basic')).toBe(true);
  });

  it('finds matches with typos', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scater', null);

    expect(results.length).toBeGreaterThan(0);
    expect(results.some(r => r.value.includes('scatter'))).toBe(true);
  });

  it('assigns matchType correctly', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', null);

    expect(results.length).toBeGreaterThan(0);
    results.forEach(result => {
      expect(['exact', 'fuzzy']).toContain(result.matchType);
    });
  });

  it('sorts exact matches before fuzzy matches', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scater', null);

    if (results.length > 1) {
      const exactIndices = results
        .map((r, i) => (r.matchType === 'exact' ? i : -1))
        .filter(i => i >= 0);
      const fuzzyIndices = results
        .map((r, i) => (r.matchType === 'fuzzy' ? i : -1))
        .filter(i => i >= 0);

      if (exactIndices.length > 0 && fuzzyIndices.length > 0) {
        const maxExactIndex = Math.max(...exactIndices);
        const minFuzzyIndex = Math.min(...fuzzyIndices);
        expect(maxExactIndex).toBeLessThan(minFuzzyIndex);
      }
    }
  });

  it('filters by selected category', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', 'spec');

    results.forEach(result => {
      expect(result.category).toBe('spec');
    });
  });

  it('excludes already selected values', () => {
    const activeFilters: ActiveFilters = [{ category: 'spec', values: ['scatter-basic'] }];
    const results = getSearchResults(mockFilterCounts, activeFilters, 'scatter', null);

    expect(results.some(r => r.value === 'scatter-basic')).toBe(false);
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
    expect(results.some(r => r.value === 'heatmap-correlation')).toBe(true);
  });

  it('includes count in results', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'scatter', null);

    expect(results.length).toBeGreaterThan(0);
    results.forEach(result => {
      expect(typeof result.count).toBe('number');
      expect(result.count).toBeGreaterThan(0);
    });
  });

  it('supports multi-word queries', () => {
    const results = getSearchResults(mockFilterCounts, emptyFilters, 'hi k', 'spec');

    expect(results.some(r => r.value === 'histogram-kde')).toBe(true);
  });
});
