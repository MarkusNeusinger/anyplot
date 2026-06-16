import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { initialHomeState, useAppData, useHomeState } from 'src/hooks/useLayoutContext';

describe('useAppData', () => {
  it('throws when used outside provider', () => {
    expect(() => {
      renderHook(() => useAppData());
    }).toThrow('useAppData must be used within AppDataProvider');
  });
});

describe('useHomeState', () => {
  it('throws when used outside provider', () => {
    expect(() => {
      renderHook(() => useHomeState());
    }).toThrow('useHomeState must be used within AppDataProvider');
  });
});

describe('initialHomeState', () => {
  it('has correct default values', () => {
    expect(initialHomeState).toEqual({
      allImages: [],
      displayedImages: [],
      activeFilters: [],
      filterCounts: null,
      globalCounts: null,
      orCounts: [],
      hasMore: false,
      scrollY: 0,
      initialized: false,
    });
  });
});
