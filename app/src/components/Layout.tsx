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

  // Fire metadata fetches immediately on mount. Previously these were wrapped
  // in requestIdleCallback to "give /plots/filter bandwidth priority", but that
  // delays the NumbersStrip ("languages / libraries / specs" counts under the
  // hero) by up to the 2 s timeout on Chrome while Safari (no rIC) ran fast —
  // explaining the user-reported "manchmal echt lange". HTTP/2 multiplexes
  // these tiny aggressively-cached responses with /plots/filter without real
  // contention, and the fetches are async so they don't block first paint.
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const load = async () => {
      try {
        const [specsRes, libsRes, langsRes, statsRes] = await Promise.all([
          fetch(`${API_URL}/specs`, { signal }),
          fetch(`${API_URL}/libraries`, { signal }),
          fetch(`${API_URL}/languages`, { signal }),
          fetch(`${API_URL}/stats`, { signal }),
        ]);

        if (signal.aborted) return;

        if (specsRes.ok) {
          const data = await specsRes.json();
          if (!signal.aborted) setSpecsData(Array.isArray(data) ? data : data.specs || []);
        }

        if (libsRes.ok) {
          const data = await libsRes.json();
          if (!signal.aborted) setLibrariesData(data.libraries || []);
        }

        if (langsRes.ok) {
          const data = await langsRes.json();
          if (!signal.aborted) setLanguagesData(data.languages || []);
        }

        if (statsRes.ok) {
          const data = await statsRes.json();
          if (!signal.aborted) setStats(data);
        }
      } catch (err) {
        if (signal.aborted) return;
        console.warn('Initial data load incomplete:', err instanceof Error ? err.message : err);
      }
    };

    load();

    return () => abortController.abort();
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
