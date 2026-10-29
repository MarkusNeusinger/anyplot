import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useMapSearch } from './useMapSearch';

describe('useMapSearch', () => {
  it('initializes state correctly', () => {
    const { result } = renderHook(() =>
      useMapSearch({
        nodeById: new Map(),
        fgRef: { current: null },
        setHoverId: vi.fn(),
        setPinnedId: vi.fn(),
        setSearchQuery: vi.fn(),
        trackEvent: vi.fn(),
      })
    );

    expect(result.current.searchOpen).toBe(false);
    expect(result.current.searchIdx).toBe(0);
    expect(result.current.searchInputRef.current).toBeNull();
  });
});
