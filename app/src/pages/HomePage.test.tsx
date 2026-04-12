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

vi.mock('../components/PlotOfTheDay', () => ({
  PlotOfTheDay: () => <div data-testid="potd">PlotOfTheDay</div>,
}));

import { HomePage } from './HomePage';

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the main components', () => {
    render(<HomePage />);
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('footer')).toBeInTheDocument();
    expect(screen.getByTestId('filterbar')).toBeInTheDocument();
  });

  it('shows PlotOfTheDay when no filters active', () => {
    render(<HomePage />);
    expect(screen.getByTestId('potd')).toBeInTheDocument();
  });

  it('renders images grid', () => {
    render(<HomePage />);
    expect(screen.getByTestId('images-grid')).toBeInTheDocument();
  });

  it('renders Helmet for SEO', () => {
    render(<HomePage />);
    expect(screen.getByTestId('helmet')).toBeInTheDocument();
  });
});
