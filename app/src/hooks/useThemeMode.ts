import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'theme';

/**
 * Manages dark/light theme via data-theme attribute on <html>.
 * Persists to localStorage, respects prefers-color-scheme on first visit.
 */
export function useThemeMode() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return false;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored === 'dark';
    return typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false;
  });

  // Sync attribute + localStorage whenever isDark changes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem(STORAGE_KEY, isDark ? 'dark' : 'light');
  }, [isDark]);

  // Listen for system preference changes (only when no explicit choice stored)
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem(STORAGE_KEY)) {
        setIsDark(e.matches);
      }
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const toggle = useCallback(() => setIsDark(prev => !prev), []);

  return { isDark, toggle } as const;
}
