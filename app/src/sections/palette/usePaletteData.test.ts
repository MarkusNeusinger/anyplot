import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { usePaletteData } from './usePaletteData';

describe('usePaletteData', () => {
  it('should return sortedPalette for imprint', () => {
    const { result } = renderHook(() => usePaletteData('imprint', null));
    expect(result.current.sortedPalette.length).toBe(8); // imprint has 8 base hues
    expect(result.current.imprintDots.length).toBe(8);
    expect(result.current.overlayDots).toBeUndefined();
  });

  it('should return sortedPalette for cvd', () => {
    const { result } = renderHook(() => usePaletteData('cvd', null));
    expect(result.current.sortedPalette.length).toBe(8);
  });

  it('should return overlay dots for okabe comparison', () => {
    const { result } = renderHook(() => usePaletteData('imprint', 'okabe'));
    expect(result.current.overlayDots?.length).toBe(7); // Okabe-Ito has 7 colors
  });
});
