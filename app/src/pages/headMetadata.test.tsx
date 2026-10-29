import { describe, expect, it, vi } from 'vitest';

import { render, screen } from 'src/test-utils';

const trackEvent = vi.fn();
const trackPageview = vi.fn();
const navigate = vi.fn();

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview }),
    useAppData: () => ({
      specsData: [],
      librariesData: [{ id: 'matplotlib', name: 'matplotlib' }],
      stats: { specs: 100, plots: 900, libraries: 9, lines_of_code: 50000 },
    }),
    useHomeState: () => ({
      homeStateRef: { current: { scrollY: 0 } },
      saveScrollPosition: vi.fn(),
    }),
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
    }),
  };
});

vi.mock('src/hooks/useFeaturedSpecs', () => ({
  useFeaturedSpecs: () => [
    {
      spec_id: 'scatter-basic',
      spec_title: 'Basic Scatter',
      spec_description: 'A scatter plot',
      library_id: 'matplotlib',
      preview_url: 'https://cdn.example.com/scatter.png',
      preview_url_light: null,
      preview_url_dark: null,
    },
  ],
}));

vi.mock('src/hooks/usePlotOfTheDay', () => ({
  usePlotOfTheDay: () => null,
}));

vi.mock('src/hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useLayoutContext')>(
    'src/hooks/useLayoutContext'
  );
  return { ...actual, useTheme: () => ({ isDark: false, toggle: vi.fn() }) };
});

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

// For PlotsPage
vi.mock('src/sections/plots-gallery/FilterBar', () => ({
  FilterBar: () => <div data-testid="filterbar">FilterBar</div>,
}));

vi.mock('src/sections/plots-gallery/ImagesGrid', () => ({
  ImagesGrid: () => <div data-testid="images-grid">ImagesGrid</div>,
}));

vi.mock('src/layouts/Footer', () => ({
  Footer: () => <div data-testid="footer">Footer</div>,
}));

// For DebugPage
vi.mock('src/lib/api', () => ({
  fetchWithAuth: vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        total_specs: 100,
        total_implementations: 500,
        coverage_percent: 85.5,
        library_stats: [
          {
            id: 'matplotlib',
            name: 'Matplotlib',
            impl_count: 80,
            avg_score: 91.5,
            min_score: 60,
            max_score: 99,
          },
        ],
        low_score_specs: [],
        oldest_specs: [],
        missing_preview_specs: [],
        missing_tags_specs: [],
        daily_impls: Array.from({ length: 30 }, (_, i) => ({
          date: `2026-04-${String(i + 1).padStart(2, '0')}`,
          impls_updated: i % 3,
        })),
        recent_activity: [],
        common_weaknesses: [],
        system: {
          database_connected: true,
          api_response_time_ms: 42,
          timestamp: '2026-04-10T12:00:00Z',
        },
        specs: [
          {
            id: 'scatter-basic',
            title: 'Basic Scatter',
            updated: '2026-04-01T12:00:00Z',
            avg_score: 95.0,
            matplotlib: 95,
            seaborn: 92,
          },
        ],
      }),
  }),
}));

import { AboutPage } from 'src/pages/AboutPage';
import { DebugPage } from 'src/pages/DebugPage';
import { LandingPage } from 'src/pages/LandingPage';
import { LegalPage } from 'src/pages/LegalPage';
import { PlotsPage } from 'src/pages/PlotsPage';

describe('Head Metadata Deduplication', () => {
  const pages = [
    { name: 'LandingPage', Component: LandingPage, expectedTitle: 'any.plot() — any library.' },
    { name: 'PlotsPage', Component: PlotsPage, expectedTitle: 'plots | anyplot.ai' },
    { name: 'AboutPage', Component: AboutPage, expectedTitle: 'about | anyplot.ai' },
    { name: 'LegalPage', Component: LegalPage, expectedTitle: 'legal | anyplot.ai' },
    { name: 'DebugPage', Component: DebugPage, expectedTitle: 'debug | anyplot.ai' },
  ];

  pages.forEach(({ name, Component, expectedTitle }) => {
    it(`renders exactly one title and at most one meta description for ${name}`, async () => {
      // Clear head before rendering to avoid interference between tests
      document.head.innerHTML = '';

      const { unmount } = render(<Component />);

      // Wait for any asynchronous state updates to settle (especially for DebugPage)
      await screen.findByText(/anyplot/i).catch(() => {});

      const titles = document.head.querySelectorAll('title');
      const descriptions = document.head.querySelectorAll('meta[name="description"]');

      expect(titles.length).toBe(1);
      expect(titles[0].textContent).toBe(expectedTitle);
      expect(descriptions.length).toBeLessThanOrEqual(1);

      unmount();
    });
  });
});
