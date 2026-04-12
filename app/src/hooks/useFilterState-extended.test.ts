import { describe, it, expect } from 'vitest';
import { isFiltersEmpty } from './useFilterState';
import type { ActiveFilters } from '../types';

describe('isFiltersEmpty - extended', () => {
  it('returns true for a single group with empty values', () => {
    const filters: ActiveFilters = [{ category: 'spec', values: [] }];
    expect(isFiltersEmpty(filters)).toBe(true);
  });

  it('returns true for many groups all with empty values', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: [] },
      { category: 'plot', values: [] },
      { category: 'spec', values: [] },
      { category: 'data', values: [] },
      { category: 'feat', values: [] },
    ];
    expect(isFiltersEmpty(filters)).toBe(true);
  });

  it('returns false when only the last group has values', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: [] },
      { category: 'plot', values: [] },
      { category: 'spec', values: ['scatter-basic'] },
    ];
    expect(isFiltersEmpty(filters)).toBe(false);
  });

  it('returns false when first group has values and rest are empty', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
      { category: 'plot', values: [] },
    ];
    expect(isFiltersEmpty(filters)).toBe(false);
  });

  it('returns false with a single group containing one value', () => {
    const filters: ActiveFilters = [
      { category: 'dep', values: ['numpy'] },
    ];
    expect(isFiltersEmpty(filters)).toBe(false);
  });

  it('returns false when all groups have values', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: ['matplotlib'] },
      { category: 'plot', values: ['scatter', 'heatmap'] },
      { category: 'feat', values: ['legend'] },
    ];
    expect(isFiltersEmpty(filters)).toBe(false);
  });

  it('handles every FilterCategory with empty values as true', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: [] },
      { category: 'spec', values: [] },
      { category: 'plot', values: [] },
      { category: 'data', values: [] },
      { category: 'dom', values: [] },
      { category: 'feat', values: [] },
      { category: 'dep', values: [] },
      { category: 'tech', values: [] },
      { category: 'pat', values: [] },
      { category: 'prep', values: [] },
      { category: 'style', values: [] },
    ];
    expect(isFiltersEmpty(filters)).toBe(true);
  });
});
