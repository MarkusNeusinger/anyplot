import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useThemeMode } from './useThemeMode';

describe('useThemeMode', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('defaults to light mode when no stored preference', () => {
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.isDark).toBe(false);
  });

  it('sets data-theme attribute on html element', () => {
    renderHook(() => useThemeMode());
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('toggles to dark mode', () => {
    const { result } = renderHook(() => useThemeMode());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('restores dark mode from localStorage', () => {
    localStorage.setItem('theme', 'dark');
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.isDark).toBe(true);
  });

  it('toggles back to light mode', () => {
    localStorage.setItem('theme', 'dark');
    const { result } = renderHook(() => useThemeMode());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isDark).toBe(false);
    expect(localStorage.getItem('theme')).toBe('light');
  });
});
