import { createContext, useContext } from 'react';
import type { PlotImage, ActiveFilters, FilterCounts } from '../types';

// Persistent home state that survives navigation
export interface HomeState {
  allImages: PlotImage[];
  displayedImages: PlotImage[];
  activeFilters: ActiveFilters;
  filterCounts: FilterCounts | null;
  globalCounts: FilterCounts | null;
  orCounts: Record<string, number>[];
  hasMore: boolean;
  scrollY: number;
  initialized: boolean;
}

export interface HomeStateContextValue {
  homeState: HomeState;
  homeStateRef: React.MutableRefObject<HomeState>;
  setHomeState: React.Dispatch<React.SetStateAction<HomeState>>;
  saveScrollPosition: () => void;
}

export interface AppData {
  specsData: import('../types').SpecInfo[];
  librariesData: import('../types').LibraryInfo[];
  stats: { specs: number; plots: number; libraries: number; lines_of_code?: number } | null;
}

export const initialHomeState: HomeState = {
  allImages: [],
  displayedImages: [],
  activeFilters: [],
  filterCounts: null,
  globalCounts: null,
  orCounts: [],
  hasMore: false,
  scrollY: 0,
  initialized: false,
};

export type ThemeMode = 'system' | 'light' | 'dark';
export type EffectiveTheme = 'light' | 'dark';

export interface ThemeContextValue {
  mode: ThemeMode;
  effective: EffectiveTheme;
  isDark: boolean;
  setMode: (mode: ThemeMode) => void;
  cycle: () => void;
}

export const AppDataContext = createContext<AppData | null>(null);
export const HomeStateContext = createContext<HomeStateContextValue | null>(null);
export const ThemeContext = createContext<ThemeContextValue>({
  mode: 'system',
  effective: 'light',
  isDark: false,
  setMode: () => {},
  cycle: () => {},
});

export function useAppData() {
  const context = useContext(AppDataContext);
  if (!context) {
    throw new Error('useAppData must be used within AppDataProvider');
  }
  return context;
}

export function useHomeState() {
  const context = useContext(HomeStateContext);
  if (!context) {
    throw new Error('useHomeState must be used within AppDataProvider');
  }
  return context;
}

export function useTheme() {
  return useContext(ThemeContext);
}
