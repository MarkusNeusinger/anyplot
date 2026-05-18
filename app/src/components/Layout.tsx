import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react';

import { API_URL } from '../constants';
import type { LanguageInfo, LibraryInfo, SpecInfo } from '../types';
import {
  AppDataContext,
  HomeStateContext,
  ThemeContext,
  initialHomeState,
  type HomeState,
} from '../hooks/useLayoutContext';
import { useThemeMode } from '../hooks/useThemeMode';

// Global provider that wraps the entire router
export function AppDataProvider({ children }: { children: ReactNode }) {
  const themeMode = useThemeMode();
  const [specsData, setSpecsData] = useState<SpecInfo[]>([]);
  const [librariesData, setLibrariesData] = useState<LibraryInfo[]>([]);
  const [languagesData, setLanguagesData] = useState<LanguageInfo[]>([]);
  const [stats, setStats] = useState<{ specs: number; plots: number; libraries: number; lines_of_code?: number } | null>(null);

  // Persistent home state (both ref for sync access and state for reactivity)
  const [homeState, setHomeState] = useState<HomeState>(initialHomeState);
  const homeStateRef = useRef<HomeState>(initialHomeState);

  // Keep ref in sync with state
  useEffect(() => {
    homeStateRef.current = homeState;
  }, [homeState]);

  // Save scroll position synchronously to ref (called before navigation)
  const saveScrollPosition = useCallback(() => {
    homeStateRef.current = { ...homeStateRef.current, scrollY: window.scrollY };
    setHomeState((prev) => ({ ...prev, scrollY: window.scrollY }));
  }, []);

  // Load shared data after browser is idle — gives /plots/filter bandwidth priority.
  // Safari/iOS doesn't ship requestIdleCallback by default, so feature-detect
  // and fall back to setTimeout — otherwise the TypeError takes the app down.
  useEffect(() => {
    const callback = async () => {
      try {
        const [specsRes, libsRes, langsRes, statsRes] = await Promise.all([
          fetch(`${API_URL}/specs`),
          fetch(`${API_URL}/libraries`),
          fetch(`${API_URL}/languages`),
          fetch(`${API_URL}/stats`),
        ]);

        if (specsRes.ok) {
          const data = await specsRes.json();
          setSpecsData(Array.isArray(data) ? data : data.specs || []);
        }

        if (libsRes.ok) {
          const data = await libsRes.json();
          setLibrariesData(data.libraries || []);
        }

        if (langsRes.ok) {
          const data = await langsRes.json();
          setLanguagesData(data.languages || []);
        }

        if (statsRes.ok) {
          const data = await statsRes.json();
          setStats(data);
        }
      } catch (err) {
        console.warn('Initial data load incomplete:', err instanceof Error ? err.message : err);
      }
    };

    const hasRIC = typeof window.requestIdleCallback === 'function';
    const id: number = hasRIC
      ? window.requestIdleCallback(callback, { timeout: 2000 })
      : window.setTimeout(callback, 1);

    return () => {
      if (hasRIC) window.cancelIdleCallback(id);
      else window.clearTimeout(id);
    };
  }, []);

  return (
    <ThemeContext.Provider value={themeMode}>
      <AppDataContext.Provider value={{ specsData, librariesData, languagesData, stats }}>
        <HomeStateContext.Provider value={{ homeState, homeStateRef, setHomeState, saveScrollPosition }}>
          {children}
        </HomeStateContext.Provider>
      </AppDataContext.Provider>
    </ThemeContext.Provider>
  );
}
