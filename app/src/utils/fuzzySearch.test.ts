import { describe, expect, it } from 'vitest';

import { createFuzzySearcher, getMatchType } from './fuzzySearch';

describe('fuzzySearch', () => {
  describe('getMatchType', () => {
    it('returns "exact" for scores below threshold (0.1)', () => {
      expect(getMatchType(0)).toBe('exact');
      expect(getMatchType(0.05)).toBe('exact');
      expect(getMatchType(0.09)).toBe('exact');
    });

    it('returns "fuzzy" for scores at or above threshold (0.1)', () => {
      expect(getMatchType(0.1)).toBe('fuzzy');
      expect(getMatchType(0.2)).toBe('fuzzy');
      expect(getMatchType(0.3)).toBe('fuzzy');
    });
  });

  describe('createFuzzySearcher', () => {
    it('finds exact matches', () => {
      const items = [
        { value: 'scatter-basic' },
        { value: 'heatmap-correlation' },
        { value: 'bar-grouped' },
      ];
      const searcher = createFuzzySearcher(items);
      const results = searcher.search('scatter');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].item.value).toBe('scatter-basic');
    });

    it('finds matches with typos (scater -> scatter)', () => {
      const items = [
        { value: 'scatter-basic' },
        { value: 'scatter-color-mapped' },
        { value: 'heatmap-correlation' },
      ];
      const searcher = createFuzzySearcher(items);
      const results = searcher.search('scater');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].item.value).toContain('scatter');
    });

    it('finds matches with typos (heatmp -> heatmap)', () => {
      const items = [
        { value: 'scatter-basic' },
        { value: 'heatmap-correlation' },
        { value: 'heatmap-annotated' },
      ];
      const searcher = createFuzzySearcher(items);
      const results = searcher.search('heatmp');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].item.value).toContain('heatmap');
    });

    it('searches in title field when provided', () => {
      const items = [
        { value: 'chessboard-pieces', title: 'Chess Board Position' },
        { value: 'scatter-basic', title: 'Basic Scatter Plot' },
      ];
      const searcher = createFuzzySearcher(items);
      const results = searcher.search('chess');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].item.value).toBe('chessboard-pieces');
    });

    it('supports multi-word AND queries', () => {
      const items = [
        { value: 'histogram-kde' },
        { value: 'histogram-basic' },
        { value: 'bar-grouped' },
      ];
      const searcher = createFuzzySearcher(items);
      const results = searcher.search('hi k');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].item.value).toBe('histogram-kde');
    });

    it('returns results with scores', () => {
      const items = [{ value: 'scatter-basic' }];
      const searcher = createFuzzySearcher(items);
      const results = searcher.search('scatter');

      expect(results[0].score).toBeDefined();
      expect(typeof results[0].score).toBe('number');
    });
  });
});
