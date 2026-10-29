import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useMapResize } from './useMapResize';

describe('useMapResize', () => {
  it('initializes with 0 size', () => {
    const { result } = renderHook(() => useMapResize());
    expect(result.current.size).toEqual({ w: 0, h: 0 });
    expect(result.current.containerRef.current).toBeNull();
  });
});
