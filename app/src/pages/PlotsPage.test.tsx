import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../test-utils';

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
    homeStateRef: { current: { scrollY: 0 } },
    saveScrollPosition: vi.fn(),
    setHomeState: vi.fn(),
    homeState: { scrollY: 0 },
  }),
  useTheme: () => ({ isDark: false, toggle: vi.fn() }),
}));

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <div data-testid="helmet">{children}</div>,
}));

vi.mock('../components/FilterBar', () => ({
  FilterBar: () => <div data-testid="filterbar">FilterBar</div>,
}));

vi.mock('../components/ImagesGrid', () => ({
  ImagesGrid: () => <div data-testid="images-grid">ImagesGrid</div>,
}));

vi.mock('../components/Footer', () => ({
  Footer: () => <div data-testid="footer">Footer</div>,
}));

import { PlotsPage } from './PlotsPage';

describe('PlotsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders FilterBar and ImagesGrid', () => {
    render(<PlotsPage />);
    expect(screen.getByTestId('filterbar')).toBeInTheDocument();
    expect(screen.getByTestId('images-grid')).toBeInTheDocument();
  });

  it('renders footer', () => {
    render(<PlotsPage />);
    expect(screen.getByTestId('footer')).toBeInTheDocument();
  });

  it('renders Helmet for SEO', () => {
    render(<PlotsPage />);
    expect(screen.getByTestId('helmet')).toBeInTheDocument();
  });
});
