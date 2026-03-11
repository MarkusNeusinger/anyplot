import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { parseUrlFilters, buildFilterUrl, useUrlSync } from './useUrlSync';
import type { ActiveFilters } from '../types';

describe('parseUrlFilters', () => {
  beforeEach(() => {
    // Reset URL to clean state
    window.history.replaceState({}, '', '/');
  });

  it('returns empty array for no params', () => {
    expect(parseUrlFilters()).toEqual([]);
  });

  it('parses single filter', () => {
    window.history.replaceState({}, '', '/?lib=matplotlib');
    expect(parseUrlFilters()).toEqual([{ category: 'lib', values: ['matplotlib'] }]);
  });

  it('parses comma-separated OR values', () => {
    window.history.replaceState({}, '', '/?lib=matplotlib,seaborn');
    expect(parseUrlFilters()).toEqual([{ category: 'lib', values: ['matplotlib', 'seaborn'] }]);
  });

  it('parses multiple AND groups', () => {
    window.history.replaceState({}, '', '/?lib=matplotlib&plot=scatter');
    const filters = parseUrlFilters();
    expect(filters).toEqual([
      { category: 'lib', values: ['matplotlib'] },
      { category: 'plot', values: ['scatter'] },
    ]);
  });

  it('parses repeated params as separate groups', () => {
    window.history.replaceState({}, '', '/?lib=matplotlib&lib=seaborn');
    const filters = parseUrlFilters();
    expect(filters).toHaveLength(2);
    expect(filters[0]).toEqual({ category: 'lib', values: ['matplotlib'] });
    expect(filters[1]).toEqual({ category: 'lib', values: ['seaborn'] });
  });

  it('ignores unknown categories', () => {
    window.history.replaceState({}, '', '/?unknown=value&lib=matplotlib');
    const filters = parseUrlFilters();
    expect(filters).toEqual([{ category: 'lib', values: ['matplotlib'] }]);
  });

  it('trims whitespace in values', () => {
    window.history.replaceState({}, '', '/?lib=matplotlib%2C%20seaborn');
    const filters = parseUrlFilters();
    expect(filters[0].values).toEqual(['matplotlib', 'seaborn']);
  });
});

describe('buildFilterUrl', () => {
  it('returns / for empty filters', () => {
    expect(buildFilterUrl([])).toBe('/');
  });

  it('builds single filter URL', () => {
    const filters: ActiveFilters = [{ category: 'lib', values: ['matplotlib'] }];
    expect(buildFilterUrl(filters)).toBe('?lib=matplotlib');
  });

  it('builds comma-separated OR values', () => {
    const filters: ActiveFilters = [{ category: 'lib', values: ['matplotlib', 'seaborn'] }];
    expect(buildFilterUrl(filters)).toBe('?lib=matplotlib%2Cseaborn');
  });

  it('builds multiple AND groups', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
      { category: 'plot', values: ['scatter'] },
    ];
    expect(buildFilterUrl(filters)).toBe('?lib=matplotlib&plot=scatter');
  });

  it('skips groups with empty values', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: [] },
      { category: 'plot', values: ['scatter'] },
    ];
    expect(buildFilterUrl(filters)).toBe('?plot=scatter');
  });
});

describe('useUrlSync', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  it('updates URL and document title', () => {
    const onTrackPageview = vi.fn();
    const filters: ActiveFilters = [{ category: 'lib', values: ['matplotlib'] }];

    renderHook(() => useUrlSync({ activeFilters: filters, onTrackPageview }));

    expect(window.location.search).toBe('?lib=matplotlib');
    expect(document.title).toBe('lib:matplotlib | pyplots.ai');
    expect(onTrackPageview).toHaveBeenCalled();
  });

  it('sets default title for no filters', () => {
    const onTrackPageview = vi.fn();

    renderHook(() => useUrlSync({ activeFilters: [], onTrackPageview }));

    expect(document.title).toBe('pyplots.ai');
  });
});
