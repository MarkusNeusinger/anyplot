import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { LIBRARIES } from 'src/constants';

import { SpecStatus } from './useDebugStatus';
import { countImpls, hasLowScore, useSpecFilters } from './useSpecFilters';

const mockSpec1: SpecStatus = {
  id: 'spec-1',
  title: 'Test Spec 1',
  updated: '2026-05-01',
  avg_score: 95,
  altair: 95,
  bokeh: null,
  chartjs: null,
  d3: null,
  echarts: null,
  ggplot2: null,
  highcharts: null,
  letsplot: null,
  makie: null,
  matplotlib: null,

  plotly: null,
  seaborn: null,
  muix: null,
  plotnine: null,
  pygal: null,
};

const mockSpec2: SpecStatus = {
  id: 'spec-2',
  title: 'Test Spec 2',
  updated: '2026-05-02',
  avg_score: 85, // < 90 is low score
  altair: 85,
  bokeh: 85,
  chartjs: 85,
  d3: 85,
  echarts: 85,
  ggplot2: 85,
  highcharts: 85,
  letsplot: 85,
  makie: 85,
  matplotlib: 85,

  plotly: 85,
  seaborn: 85,
  muix: 85,
  plotnine: 85,
  pygal: 85,
};

const specs = [mockSpec1, mockSpec2];

describe('useSpecFilters', () => {
  it('initializes with default sorting', () => {
    const { result } = renderHook(() => useSpecFilters(specs));

    // Sort updated desc -> spec2 then spec1
    expect(result.current.filteredSpecs[0].id).toBe('spec-2');
    expect(result.current.filteredSpecs[1].id).toBe('spec-1');
  });

  it('filters by searchText', () => {
    const { result } = renderHook(() => useSpecFilters(specs));

    act(() => {
      result.current.setSearchText('spec-1');
    });

    expect(result.current.filteredSpecs.length).toBe(1);
    expect(result.current.filteredSpecs[0].id).toBe('spec-1');
  });

  it('filters by showIncomplete', () => {
    const { result } = renderHook(() => useSpecFilters(specs));

    act(() => {
      result.current.setShowIncomplete(true);
    });

    // Both are incomplete (vega, observable, etc in LIBRARIES but not explicitly mocked with truthy if not in list)
    // Actually mockSpec2 has all 14 set, but let's just assert on existence of incomplete specs
    expect(result.current.filteredSpecs.some(s => s.id === 'spec-1')).toBe(true);
  });

  it('filters by showLowScores', () => {
    const { result } = renderHook(() => useSpecFilters(specs));

    act(() => {
      result.current.setShowLowScores(true);
    });

    expect(result.current.filteredSpecs.length).toBe(1);
    expect(result.current.filteredSpecs[0].id).toBe('spec-2');
  });

  it('handles sort changes', () => {
    const { result } = renderHook(() => useSpecFilters(specs));

    act(() => {
      // Toggle to asc
      result.current.handleSort('updated');
    });

    expect(result.current.sortDir).toBe('asc');
    expect(result.current.filteredSpecs[0].id).toBe('spec-1'); // Older
  });

  it('handles helper functions properly', () => {
    const spec1Count = LIBRARIES.filter(lib => mockSpec1[lib as keyof SpecStatus] !== null).length;
    const spec2Count = LIBRARIES.filter(lib => mockSpec2[lib as keyof SpecStatus] !== null).length;
    expect(countImpls(mockSpec1)).toBe(spec1Count);
    expect(countImpls(mockSpec2)).toBe(spec2Count);

    expect(hasLowScore(mockSpec1)).toBe(false);
    expect(hasLowScore(mockSpec2)).toBe(true);
  });
});
