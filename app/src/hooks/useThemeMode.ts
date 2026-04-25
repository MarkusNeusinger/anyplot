import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'theme';

export type ThemeMode = 'system' | 'light' | 'dark';
export type EffectiveTheme = 'light' | 'dark';

const CYCLE: ThemeMode[] = ['system', 'light', 'dark'];

function readStoredMode(): ThemeMode {
  if (typeof window === 'undefined') return 'system';
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === 'dark' || stored === 'light' ? stored : 'system';
}

function systemPrefersDark(): boolean {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function persistMode(mode: ThemeMode): void {
  if (mode === 'system') localStorage.removeItem(STORAGE_KEY);
  else localStorage.setItem(STORAGE_KEY, mode);
}

/**
 * Tri-state theme hook (system/light/dark).
 *
 * - `system` (default): follows `prefers-color-scheme` live and writes nothing
 *   to localStorage, so a fresh visit on a new device or browser keeps tracking
 *   the OS until the user opts in.
 * - `light` / `dark`: explicit user choice, persisted in localStorage and
 *   immune to OS-level changes during the session.
 * - Returning to `system` clears the storage key, so the next visit again
 *   defaults to OS-following.
 */
export function useThemeMode() {
  const [mode, setModeState] = useState<ThemeMode>(readStoredMode);
  const [systemDark, setSystemDark] = useState<boolean>(systemPrefersDark);

  const effective: EffectiveTheme = mode === 'system'
    ? (systemDark ? 'dark' : 'light')
    : mode;

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', effective);
  }, [effective]);

  // Track OS preference unconditionally — the value only feeds `effective` while
  // mode === 'system', but keeping the listener mounted means re-entering
  // system mode picks up the current OS state without a stale reading.
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const setMode = useCallback((next: ThemeMode) => {
    persistMode(next);
    setModeState(next);
  }, []);

  const cycle = useCallback(() => {
    setModeState(prev => {
      const next = CYCLE[(CYCLE.indexOf(prev) + 1) % CYCLE.length];
      persistMode(next);
      return next;
    });
  }, []);

  return {
    mode,
    effective,
    isDark: effective === 'dark',
    setMode,
    cycle,
  } as const;
}
