import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { usePaletteState } from './usePaletteState';

describe('usePaletteState', () => {
  it('should initialize with default values', () => {
    const { result } = renderHook(() => usePaletteState());
    expect(result.current.lang).toBe('python');
    expect(result.current.oklch).toBe(false);
    expect(result.current.compareId).toBeNull();
    expect(result.current.sort).toBe('imprint');
    expect(result.current.copiedHex).toBeNull();
    expect(result.current.wheelOpen).toBe(false);
  });

  it('should update state', () => {
    const { result } = renderHook(() => usePaletteState());

    act(() => {
      result.current.setLang('js');
    });
    expect(result.current.lang).toBe('js');

    act(() => {
      result.current.setWheelOpen(true);
    });
    expect(result.current.wheelOpen).toBe(true);
  });
});
