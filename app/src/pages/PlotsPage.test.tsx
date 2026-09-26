import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fireEvent, render, screen } from 'src/test-utils';

const { mockHandleRandom, mockTrackEvent, state } = vi.hoisted(() => ({
  mockHandleRandom: vi.fn(),
  mockTrackEvent: vi.fn(),
  state: {
    activeFilters: [] as { category: string; values: string[] }[],
    specsData: [] as { id: string; title: string }[],
    specTitles: {} as Record<string, string>,
  },
}));

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: mockTrackEvent }),
  useInfiniteScroll: () => ({ loadMoreRef: { current: null } }),
  useFilterState: () => ({
    activeFilters: state.activeFilters,
    filterCounts: null,
    globalCounts: null,
    orCounts: [],
    specTitles: state.specTitles,
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
    handleRandom: mockHandleRandom,
    randomAnimation: null,
  }),
  isFiltersEmpty: (f: unknown[]) => !f || f.length === 0,
  useAppData: () => ({ specsData: state.specsData, librariesData: [], stats: null }),
  useHomeState: () => ({
    homeStateRef: { current: { scrollY: 0 } },
    saveScrollPosition: vi.fn(),
    setHomeState: vi.fn(),
    homeState: { scrollY: 0 },
  }),
  useTheme: () => ({ isDark: false, toggle: vi.fn() }),
}));

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="helmet">{children}</div>
  ),
}));

vi.mock('src/sections/plots-gallery/FilterBar', () => ({
  FilterBar: () => <div data-testid="filterbar">FilterBar</div>,
}));

vi.mock('src/sections/plots-gallery/ImagesGrid', () => ({
  ImagesGrid: () => <div data-testid="images-grid">ImagesGrid</div>,
}));

vi.mock('src/layouts/Footer', () => ({
  Footer: () => <div data-testid="footer">Footer</div>,
}));

import { PlotsPage } from 'src/pages/PlotsPage';

describe('PlotsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    state.activeFilters = [];
    state.specsData = [];
    state.specTitles = {};
  });

  describe('link to the spec page', () => {
    const MANHATTAN = { id: 'manhattan-gwas', title: 'Manhattan Plot for GWAS' };

    it('links the spec page when the gallery is filtered to exactly one spec', () => {
      state.activeFilters = [{ category: 'spec', values: ['manhattan-gwas'] }];
      state.specsData = [MANHATTAN];
      state.specTitles = { 'manhattan-gwas': MANHATTAN.title };
      render(<PlotsPage />);
      const link = screen.getByRole('link', {
        name: 'Compare all implementations of Manhattan Plot for GWAS',
      });
      expect(link).toHaveAttribute('href', '/manhattan-gwas');
      expect(link).toHaveTextContent('manhattan-gwas.compare()');
    });

    it('tracks the click as nav_click from the gallery', () => {
      state.activeFilters = [{ category: 'spec', values: ['manhattan-gwas'] }];
      state.specsData = [MANHATTAN];
      render(<PlotsPage />);
      fireEvent.click(screen.getByRole('link', { name: /compare all implementations/i }));
      expect(mockTrackEvent).toHaveBeenCalledWith('nav_click', {
        source: 'gallery_spec_hub',
        target: '/manhattan-gwas',
        spec: 'manhattan-gwas',
      });
    });

    it.each([
      ['no filter', []],
      ['a non-spec filter', [{ category: 'lib', values: ['matplotlib'] }]],
      ['OR-combined specs', [{ category: 'spec', values: ['manhattan-gwas', 'scatter-basic'] }]],
      [
        'AND-combined specs',
        [
          { category: 'spec', values: ['manhattan-gwas'] },
          { category: 'spec', values: ['scatter-basic'] },
        ],
      ],
      ['an unknown spec id', [{ category: 'spec', values: ['no-such-spec'] }]],
    ])('offers no link with %s', (_, filters) => {
      state.activeFilters = filters;
      state.specsData = [MANHATTAN, { id: 'scatter-basic', title: 'Basic Scatter Plot' }];
      render(<PlotsPage />);
      expect(screen.queryByRole('link', { name: /compare all implementations/i })).toBeNull();
    });
  });

  it('renders FilterBar and ImagesGrid', () => {
    render(<PlotsPage />);
    expect(screen.getByTestId('filterbar')).toBeInTheDocument();
    expect(screen.getByTestId('images-grid')).toBeInTheDocument();
  });

  it('renders Helmet for SEO', () => {
    render(<PlotsPage />);
    expect(screen.getByTestId('helmet')).toBeInTheDocument();
  });

  it('renders the shared scroll-to-top button', () => {
    render(<PlotsPage />);
    expect(screen.getByLabelText(/scroll to top/i)).toBeInTheDocument();
  });

  describe('global keyboard shortcuts', () => {
    it('triggers random navigation on Space when nothing interactive is focused', () => {
      render(<PlotsPage />);
      fireEvent.keyDown(document.body, { key: ' ' });
      expect(mockHandleRandom).toHaveBeenCalledWith('space');
    });

    it('does not fire when a focusable card owns the keystroke', () => {
      render(<PlotsPage />);
      const card = document.createElement('div');
      card.setAttribute('role', 'button');
      card.tabIndex = 0;
      document.body.appendChild(card);
      try {
        fireEvent.keyDown(card, { key: ' ' });
        expect(mockHandleRandom).not.toHaveBeenCalled();
      } finally {
        card.remove();
      }
    });

    it('does not fire when a native button owns the keystroke', () => {
      render(<PlotsPage />);
      const button = document.createElement('button');
      document.body.appendChild(button);
      try {
        fireEvent.keyDown(button, { key: ' ' });
        expect(mockHandleRandom).not.toHaveBeenCalled();
      } finally {
        button.remove();
      }
    });
  });

  describe('scrollRestoration', () => {
    const original = history.scrollRestoration;

    afterEach(() => {
      history.scrollRestoration = original;
    });

    it("sets scrollRestoration to 'manual' on mount and restores the previous value on unmount", () => {
      history.scrollRestoration = 'auto';
      const { unmount } = render(<PlotsPage />);
      expect(history.scrollRestoration).toBe('manual');
      unmount();
      expect(history.scrollRestoration).toBe('auto');
    });

    it('restores a non-default previous value on unmount instead of forcing auto', () => {
      history.scrollRestoration = 'manual';
      const { unmount } = render(<PlotsPage />);
      expect(history.scrollRestoration).toBe('manual');
      unmount();
      expect(history.scrollRestoration).toBe('manual');
    });
  });
});
