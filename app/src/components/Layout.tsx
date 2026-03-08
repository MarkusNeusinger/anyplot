import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react';
import { Outlet } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';

import { API_URL } from '../constants';
import type { LibraryInfo, SpecInfo } from '../types';
import {
  AppDataContext,
  HomeStateContext,
  initialHomeState,
  type HomeState,
} from '../hooks/useLayoutContext';

// Global provider that wraps the entire router (persists across all pages including InteractivePage)
export function AppDataProvider({ children }: { children: ReactNode }) {
  const [specsData, setSpecsData] = useState<SpecInfo[]>([]);
  const [librariesData, setLibrariesData] = useState<LibraryInfo[]>([]);
  const [stats, setStats] = useState<{ specs: number; plots: number; libraries: number } | null>(null);

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

  // Load shared data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [specsRes, libsRes, statsRes] = await Promise.all([
          fetch(`${API_URL}/specs`),
          fetch(`${API_URL}/libraries`),
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

        if (statsRes.ok) {
          const data = await statsRes.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Error loading initial data:', err);
      }
    };
    fetchData();
  }, []);

  return (
    <AppDataContext.Provider value={{ specsData, librariesData, stats }}>
      <HomeStateContext.Provider value={{ homeState, homeStateRef, setHomeState, saveScrollPosition }}>
        {children}
      </HomeStateContext.Provider>
    </AppDataContext.Provider>
  );
}

// Layout component for pages with standard layout (HomePage, SpecPage, CatalogPage)
export function Layout() {
  return (
    <>
      <Helmet>
        <meta name="robots" content="index, follow" />
      </Helmet>
      <Box component="main" sx={{ minHeight: '100vh', bgcolor: '#fafafa', py: 5, position: 'relative' }}>
        <Container maxWidth={false} sx={{ px: { xs: 2, sm: 4, md: 8, lg: 12 } }}>
          <Outlet />
        </Container>
      </Box>
    </>
  );
}
