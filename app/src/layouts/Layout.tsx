import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';

import {
  AppDataContext,
  type HomeState,
  HomeStateContext,
  initialHomeState,
  ThemeContext,
} from 'src/hooks/useLayoutContext';
import { useThemeMode } from 'src/hooks/useThemeMode';
import { ApiError, apiGet, endpoints } from 'src/lib/api';
import type { LanguageInfo, LibraryInfo, SpecInfo } from 'src/types';

// Global provider that wraps the entire router
export function AppDataProvider({ children }: { children: ReactNode }) {
  const themeMode = useThemeMode();
  const [specsData, setSpecsData] = useState<SpecInfo[]>([]);
  const [librariesData, setLibrariesData] = useState<LibraryInfo[]>([]);
  const [languagesData, setLanguagesData] = useState<LanguageInfo[]>([]);
  const [stats, setStats] = useState<{
    specs: number;
    plots: number;
    libraries: number;
    lines_of_code?: number;
  } | null>(null);

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
    setHomeState(prev => ({ ...prev, scrollY: window.scrollY }));
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
      // Non-ok responses used to be skipped per endpoint (res.ok check) while
      // the other setters still ran; map ApiError to null to keep that, and
      // rethrow everything else (network errors, aborts) so the whole load
      // lands in the outer catch like before.
      const safeGet = async <T,>(path: string): Promise<T | null> => {
        try {
          return await apiGet<T>(path, { signal });
        } catch (err) {
          if (err instanceof ApiError) return null;
          throw err;
        }
      };

      try {
        const [specsBody, libsBody, langsBody, statsBody] = await Promise.all([
          safeGet<SpecInfo[] | { specs?: SpecInfo[] }>(endpoints.specs),
          safeGet<{ libraries?: LibraryInfo[] }>(endpoints.libraries),
          safeGet<{ languages?: LanguageInfo[] }>(endpoints.languages),
          safeGet<{ specs: number; plots: number; libraries: number; lines_of_code?: number }>(
            endpoints.stats
          ),
        ]);

        if (signal.aborted) return;

        if (specsBody) setSpecsData(Array.isArray(specsBody) ? specsBody : specsBody.specs || []);
        if (libsBody) setLibrariesData(libsBody.libraries || []);
        if (langsBody) setLanguagesData(langsBody.languages || []);
        if (statsBody) setStats(statsBody);
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
        <HomeStateContext.Provider
          value={{ homeState, homeStateRef, setHomeState, saveScrollPosition }}
        >
          {children}
        </HomeStateContext.Provider>
      </AppDataContext.Provider>
    </ThemeContext.Provider>
  );
}
