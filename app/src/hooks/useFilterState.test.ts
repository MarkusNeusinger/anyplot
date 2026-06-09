import { describe, expect, it } from 'vitest';

import type { ActiveFilters } from '../types';
import { isFiltersEmpty } from './useFilterState';

describe('isFiltersEmpty', () => {
  it('returns true for empty array', () => {
    expect(isFiltersEmpty([])).toBe(true);
  });

  it('returns true when all groups have empty values', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: [] },
      { category: 'plot', values: [] },
    ];
    expect(isFiltersEmpty(filters)).toBe(true);
  });

  it('returns false when any group has values', () => {
    const filters: ActiveFilters = [{ category: 'lib', values: ['matplotlib'] }];
    expect(isFiltersEmpty(filters)).toBe(false);
  });

  it('returns false when mixed empty and non-empty groups', () => {
    const filters: ActiveFilters = [
      { category: 'lib', values: [] },
      { category: 'plot', values: ['scatter'] },
    ];
    expect(isFiltersEmpty(filters)).toBe(false);
  });

  it('returns false with multiple values in a group', () => {
    const filters: ActiveFilters = [{ category: 'lib', values: ['matplotlib', 'seaborn'] }];
    expect(isFiltersEmpty(filters)).toBe(false);
  });
});
