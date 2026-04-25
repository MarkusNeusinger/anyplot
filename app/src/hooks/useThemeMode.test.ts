import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useThemeMode } from './useThemeMode';

type MQListener = (e: MediaQueryListEvent) => void;

interface MockMediaQuery {
  matches: boolean;
  media: string;
  addEventListener: (type: 'change', listener: MQListener) => void;
  removeEventListener: (type: 'change', listener: MQListener) => void;
  // Test-only helpers
  _emit: (matches: boolean) => void;
}

function installMatchMedia(initialDark: boolean) {
  let matches = initialDark;
  const listeners = new Set<MQListener>();
  const mq: MockMediaQuery = {
    get matches() { return matches; },
    set matches(v: boolean) { matches = v; },
    media: '(prefers-color-scheme: dark)',
    addEventListener: (_type, listener) => { listeners.add(listener); },
    removeEventListener: (_type, listener) => { listeners.delete(listener); },
    _emit(next: boolean) {
      matches = next;
      const event = { matches: next, media: mq.media } as MediaQueryListEvent;
      listeners.forEach(l => l(event));
    },
  };
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue(mq));
  return mq;
}

describe('useThemeMode', () => {
  let mq: MockMediaQuery;

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    mq = installMatchMedia(false);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('first-ever visit defaults to system mode and persists nothing', () => {
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.mode).toBe('system');
    expect(result.current.effective).toBe('light');
    expect(result.current.isDark).toBe(false);
    expect(localStorage.getItem('theme')).toBeNull();
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('system mode follows the OS preference at mount', () => {
    mq._emit(true); // OS prefers dark before mount
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.mode).toBe('system');
    expect(result.current.effective).toBe('dark');
    expect(localStorage.getItem('theme')).toBeNull();
  });

  it('system → light transition persists the choice', () => {
    const { result } = renderHook(() => useThemeMode());

    act(() => { result.current.cycle(); });

    expect(result.current.mode).toBe('light');
    expect(result.current.effective).toBe('light');
    expect(localStorage.getItem('theme')).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('light → dark transition persists the new choice', () => {
    localStorage.setItem('theme', 'light');
    const { result } = renderHook(() => useThemeMode());

    act(() => { result.current.cycle(); });

    expect(result.current.mode).toBe('dark');
    expect(result.current.effective).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('dark → system transition clears localStorage and re-follows the OS', () => {
    localStorage.setItem('theme', 'dark');
    mq._emit(false); // OS prefers light
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.mode).toBe('dark');

    act(() => { result.current.cycle(); });

    expect(result.current.mode).toBe('system');
    expect(result.current.effective).toBe('light');
    expect(localStorage.getItem('theme')).toBeNull();
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('live OS change flips the theme while in system mode', () => {
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.effective).toBe('light');

    act(() => { mq._emit(true); });

    expect(result.current.effective).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(localStorage.getItem('theme')).toBeNull();
  });

  it('explicit light/dark mode ignores OS-level changes', () => {
    localStorage.setItem('theme', 'light');
    const { result } = renderHook(() => useThemeMode());

    act(() => { mq._emit(true); }); // OS flips to dark — should be ignored

    expect(result.current.mode).toBe('light');
    expect(result.current.effective).toBe('light');
  });

  it('setMode jumps directly to a target mode', () => {
    const { result } = renderHook(() => useThemeMode());

    act(() => { result.current.setMode('dark'); });
    expect(result.current.mode).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');

    act(() => { result.current.setMode('system'); });
    expect(result.current.mode).toBe('system');
    expect(localStorage.getItem('theme')).toBeNull();
  });

  it('restores explicit dark mode from localStorage on remount', () => {
    localStorage.setItem('theme', 'dark');
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.mode).toBe('dark');
    expect(result.current.effective).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
});
