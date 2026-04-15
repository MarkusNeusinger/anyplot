import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../test-utils';

// Mock hooks
vi.mock('../hooks', () => ({
  useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: vi.fn() }),
  useInfiniteScroll: () => ({ loadMoreRef: { current: null } }),
  useFilterState: () => ({
    activeFilters: [],
    filterCounts: null,
    globalCounts: null,
    orCounts: [],
    specTitles: {},
    allImages: [],
    displayedImages: [],
    hasMore: false,
    loading: false,
    error: '',
    setDisplayedImages: vi.fn(),
    setHasMore: vi.fn(),
    setError: vi.fn(),
    handleAddFilter: vi.fn(),
    handleAddValueToGroup: vi.fn(),
    handleRemoveFilter: vi.fn(),
    handleRemoveGroup: vi.fn(),
    handleRandom: vi.fn(),
    randomAnimation: null,
  }),
  isFiltersEmpty: (f: unknown[]) => !f || f.length === 0,
  useAppData: () => ({ specsData: [], librariesData: [], stats: null }),
  useHomeState: () => ({
    homeStateRef: { current: { scrollY: 0, imageSize: 'normal', searchExpanded: false } },
    saveScrollPosition: vi.fn(),
    setHomeState: vi.fn(),
    homeState: { scrollY: 0, imageSize: 'normal', searchExpanded: false },
  }),
  useTheme: () => ({ isDark: false, toggle: vi.fn() }),
}));

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <div data-testid="helmet">{children}</div>,
}));

vi.mock('../components/Header', () => ({
  Header: () => <div data-testid="header">Header</div>,
}));

vi.mock('../components/Footer', () => ({
  Footer: () => <div data-testid="footer">Footer</div>,
}));

vi.mock('../components/FilterBar', () => ({
  FilterBar: () => <div data-testid="filterbar">FilterBar</div>,
}));

vi.mock('../components/ImagesGrid', () => ({
  ImagesGrid: () => <div data-testid="images-grid">ImagesGrid</div>,
}));

// Hero section components (shown when no filters and scrollY === 0)
vi.mock('../components/MastheadRule', () => ({
  MastheadRule: () => <div data-testid="masthead">MastheadRule</div>,
}));

vi.mock('../components/HeroSection', () => ({
  HeroSection: () => <div data-testid="hero">HeroSection</div>,
}));

vi.mock('../components/NumbersStrip', () => ({
  NumbersStrip: () => <div data-testid="numbers">NumbersStrip</div>,
}));

vi.mock('../components/LibrariesSection', () => ({
  LibrariesSection: () => <div data-testid="libraries">LibrariesSection</div>,
}));

vi.mock('../components/CodeShowcase', () => ({
  CodeShowcase: () => <div data-testid="code-showcase">CodeShowcase</div>,
}));

vi.mock('../components/ScienceNote', () => ({
  ScienceNote: () => <div data-testid="science">ScienceNote</div>,
}));

import { HomePage } from './HomePage';

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders hero sections when no filters active (fresh page load)', () => {
    render(<HomePage />);
    expect(screen.getByTestId('masthead')).toBeInTheDocument();
    expect(screen.getByTestId('hero')).toBeInTheDocument();
    expect(screen.getByTestId('numbers')).toBeInTheDocument();
    expect(screen.getByTestId('libraries')).toBeInTheDocument();
    expect(screen.getByTestId('code-showcase')).toBeInTheDocument();
    expect(screen.getByTestId('science')).toBeInTheDocument();
  });

  it('renders catalog components (filterbar, grid, footer)', () => {
    render(<HomePage />);
    expect(screen.getByTestId('filterbar')).toBeInTheDocument();
    expect(screen.getByTestId('images-grid')).toBeInTheDocument();
    expect(screen.getByTestId('footer')).toBeInTheDocument();
  });

  it('hides header when hero is shown', () => {
    render(<HomePage />);
    // Hero is shown (scrollY=0, no filters), so Header should NOT be rendered
    expect(screen.queryByTestId('header')).toBeNull();
  });

  it('renders Helmet for SEO', () => {
    render(<HomePage />);
    expect(screen.getByTestId('helmet')).toBeInTheDocument();
  });
});
