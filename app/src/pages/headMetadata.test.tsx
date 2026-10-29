import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AboutPage } from 'src/pages/AboutPage';
import { DebugPage } from 'src/pages/DebugPage';
import { LandingPage } from 'src/pages/LandingPage';
import { LegalPage } from 'src/pages/LegalPage';
import { PlotsPage } from 'src/pages/PlotsPage';
import { render } from 'src/test-utils';
import { removeShellDefaults } from 'src/utils/shellMetadata';

vi.mock('src/hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useLayoutContext')>(
    'src/hooks/useLayoutContext'
  );
  return {
    ...actual,
    useTheme: () => ({ isDark: false, toggle: vi.fn() }),
    useAppData: () => ({
      specs: [],
      specTitles: {},
      filterCounts: null,
      globalCounts: null,
      fetchError: null,
      hasData: true,
      lastUpdated: '2023-01-01',
    }),
    useHomeState: () => ({
      specsData: [],
      specTitles: {},
      allImages: [],
      displayedImages: [],
      activeFilters: [],
      filterCounts: null,
      globalCounts: null,
      orCounts: [],
      hasMore: false,
      loading: false,
      error: '',
      setDisplayedImages: vi.fn(),
      handleFilterClick: vi.fn(),
      handleSortModeChange: vi.fn(),
      loadMore: vi.fn(),
      homeStateRef: { current: { scrollY: 0 } },
      saveScrollPosition: vi.fn(),
    }),
  };
});

vi.mock('src/hooks/useFeaturedSpecs', () => ({
  useFeaturedSpecs: () => [],
}));

vi.mock('src/hooks/usePlotOfTheDay', () => ({
  usePlotOfTheDay: () => null,
}));

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: vi.fn() }),
    useAppData: () => ({
      specs: [],
      specTitles: {},
      filterCounts: null,
      globalCounts: null,
      fetchError: null,
      hasData: true,
      lastUpdated: '2023-01-01',
    }),
    useHomeState: () => ({
      specsData: [],
      specTitles: {},
      allImages: [],
      displayedImages: [],
      activeFilters: [],
      filterCounts: null,
      globalCounts: null,
      orCounts: [],
      hasMore: false,
      loading: false,
      error: '',
      setDisplayedImages: vi.fn(),
      handleFilterClick: vi.fn(),
      handleSortModeChange: vi.fn(),
      loadMore: vi.fn(),
      homeStateRef: { current: { scrollY: 0 } },
      saveScrollPosition: vi.fn(),
    }),
  };
});

// For PlotsPage filters and infinite scroll context
vi.mock('src/hooks/useFilterState', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useFilterState')>(
    'src/hooks/useFilterState'
  );
  return {
    ...actual,
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
      handleFilterClick: vi.fn(),
      handleSortModeChange: vi.fn(),
      loadMore: vi.fn(),
    }),
  };
});

vi.mock('src/hooks/useInfiniteScroll', () => ({
  useInfiniteScroll: () => ({ loadMoreRef: { current: null } }),
}));

vi.mock('src/sections/landing/LibrariesSection', () => ({
  LibrariesSection: () => <div data-testid="libraries-section" />,
}));
vi.mock('src/sections/landing/HeroSection', () => ({
  HeroSection: () => <div data-testid="hero" />,
}));
vi.mock('src/sections/landing/NumbersStrip', () => ({
  NumbersStrip: () => <div data-testid="numbers" />,
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
vi.mock('src/utils/filters', async () => {
  const actual = await vi.importActual<typeof import('src/utils/filters')>('src/utils/filters');
  return { ...actual };
});

describe('head metadata deduplication', () => {
  beforeEach(() => {
    // Clear head
    document.head.innerHTML = '';

    // Insert the 6 marked shell tags
    const tags = [
      { tag: 'title', attrs: {} },
      { tag: 'meta', attrs: { name: 'description', content: 'desc' } },
      { tag: 'meta', attrs: { property: 'og:title', content: 'og title' } },
      { tag: 'meta', attrs: { property: 'og:description', content: 'og desc' } },
      { tag: 'meta', attrs: { name: 'twitter:title', content: 'tw title' } },
      { tag: 'meta', attrs: { name: 'twitter:description', content: 'tw desc' } },
    ];

    tags.forEach(({ tag, attrs }) => {
      const el = document.createElement(tag);
      el.setAttribute('data-shell-default', '');
      Object.entries(attrs).forEach(([key, val]) => el.setAttribute(key, val));
      if (tag === 'title') {
        el.textContent = 'shell title';
      }
      document.head.appendChild(el);
    });
  });

  afterEach(() => {
    document.head.innerHTML = '';
  });

  it('LandingPage deduplicates head tags', () => {
    removeShellDefaults();
    const { unmount } = render(<LandingPage />);

    const titles = document.head.querySelectorAll('title');
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toBe('any.plot() — any library.');

    const descs = document.head.querySelectorAll('meta[name="description"]');
    expect(descs.length).toBeLessThanOrEqual(1);
    unmount();
  });

  it('PlotsPage deduplicates head tags', () => {
    removeShellDefaults();
    const { unmount } = render(<PlotsPage />);

    const titles = document.head.querySelectorAll('title');
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toBe('plots | anyplot.ai');

    const descs = document.head.querySelectorAll('meta[name="description"]');
    expect(descs.length).toBeLessThanOrEqual(1);
    unmount();
  });

  it('AboutPage deduplicates head tags', () => {
    removeShellDefaults();
    const { unmount } = render(<AboutPage />);

    const titles = document.head.querySelectorAll('title');
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toBe('about | anyplot.ai');

    const descs = document.head.querySelectorAll('meta[name="description"]');
    expect(descs.length).toBeLessThanOrEqual(1);
    unmount();
  });

  it('LegalPage deduplicates head tags', () => {
    removeShellDefaults();
    const { unmount } = render(<LegalPage />);

    const titles = document.head.querySelectorAll('title');
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toBe('legal | anyplot.ai');

    const descs = document.head.querySelectorAll('meta[name="description"]');
    expect(descs.length).toBeLessThanOrEqual(1);
    unmount();
  });

  it('DebugPage deduplicates head tags', () => {
    removeShellDefaults();
    const { unmount } = render(<DebugPage />);

    const titles = document.head.querySelectorAll('title');
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toBe('debug | anyplot.ai');

    const descs = document.head.querySelectorAll('meta[name="description"]');
    expect(descs.length).toBeLessThanOrEqual(1);
    unmount();
  });
});
