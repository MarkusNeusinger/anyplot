import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, userEvent, waitFor } from '../test-utils';
import { StatsPage } from './StatsPage';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockTrackEvent = vi.fn();

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: mockTrackEvent,
  }),
}));

const mockDashboard = {
  total_specs: 142,
  total_implementations: 987,
  total_interactive: 53,
  total_lines_of_code: 245_600,
  avg_quality_score: 82.5,
  coverage_percent: 73,
  library_stats: [
    {
      id: 'matplotlib',
      name: 'matplotlib',
      impl_count: 120,
      avg_score: 85,
      min_score: 60,
      max_score: 98,
      score_buckets: { '50-55': 1, '75-80': 10, '90-95': 5 },
      loc_buckets: { '0-20': 2, '40-60': 5 },
      avg_loc: 78,
    },
  ],
  coverage_matrix: [
    {
      spec_id: 'scatter-basic',
      title: 'Basic Scatter Plot',
      libraries: {
        matplotlib: { score: 90, has_impl: true },
        plotly: { score: null, has_impl: false },
      },
    },
  ],
  top_implementations: [
    {
      spec_id: 'scatter-basic',
      spec_title: 'Basic Scatter Plot',
      library_id: 'matplotlib',
      language: 'python',
      quality_score: 95,
      preview_url: 'https://example.com/img.png',
    },
  ],
  tag_distribution: {
    plot_type: { scatter: 42, line: 30 },
    // "time series" has a space so the tag-link test below can assert
    // encodeURIComponent is actually exercised (href -> data=time%20series).
    data_type: { numeric: 80, 'time series': 12 },
  },
  score_distribution: { '50-60': 5, '60-70': 10, '70-80': 20, '80-90': 30, '90-100': 15 },
  timeline: [
    { month: '2025-01', count: 10 },
    { month: '2025-02', count: 20 },
  ],
  daily_impls: [
    { date: '2026-04-14', count: 3 },
    { date: '2026-04-15', count: 5 },
    { date: '2026-04-16', count: 0 },
  ],
};

const mockVisitors = {
  points: [
    { date: '2026-04-14', visitors: 12 },
    { date: '2026-04-15', visitors: 25 },
    { date: '2026-04-16', visitors: 7 },
  ],
};

/**
 * StatsPage performs two independent fetches: /insights/dashboard and
 * /insights/visitors. Route by URL so the visitors response isn't silently
 * replaced by the dashboard payload (and vice versa).
 */
function mockFetchSuccess(visitorsPayload: { points: Array<{ date: string; visitors: number }> } | null = mockVisitors) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      if (url.includes('/insights/visitors')) {
        return Promise.resolve({
          ok: visitorsPayload !== null,
          json: () => Promise.resolve(visitorsPayload ?? { points: [] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDashboard),
      });
    }),
  );
}

function mockFetchError() {
  // /insights/dashboard fails; visitors fetch can succeed-with-empty so the
  // visitors `useEffect` resolves cleanly and the test asserts on the
  // dashboard error path only.
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      if (url.includes('/insights/visitors')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ points: [] }) });
      }
      return Promise.resolve({ ok: false, status: 500 });
    }),
  );
}

describe('StatsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockTrackEvent.mockClear();
  });

  // vi.restoreAllMocks() doesn't undo vi.stubGlobal — without this hook the
  // mocked `fetch` would leak into other test suites in the same worker.
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders loading state initially', () => {
    // fetch never resolves so component stays in loading
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));

    render(<StatsPage />);

    expect(screen.getByText('loading stats...')).toBeInTheDocument();
  });

  it('renders dashboard with mock data after fetch', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('specifications')).toBeInTheDocument();
    });

    expect(screen.getByText('implementations')).toBeInTheDocument();
    expect(screen.getByText('libraries')).toBeInTheDocument();
    // "coverage" appears both as a stat card label and as a section heading
    expect(screen.getAllByText('coverage').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('top rated')).toBeInTheDocument();
    expect(screen.getByText('tags')).toBeInTheDocument();
  });

  it('handles fetch error gracefully', async () => {
    mockFetchError();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load stats/)).toBeInTheDocument();
    });
  });

  it('shows all 6 summary stat values', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('specifications')).toBeInTheDocument();
    });

    // total_specs: 142
    expect(screen.getByText('142')).toBeInTheDocument();
    // total_implementations: 987
    expect(screen.getByText('987')).toBeInTheDocument();
    // total_interactive: 53
    expect(screen.getByText('53')).toBeInTheDocument();
    // total_lines_of_code: 245600 => formatNum => "245.6K"
    expect(screen.getByText('245.6K')).toBeInTheDocument();
    // avg_quality_score: 82.5 => formatNum(82.5) => locale-sensitive decimal separator
    expect(screen.getByText(/82[.,]5/)).toBeInTheDocument();
    // coverage_percent: 73 => "73%"
    expect(screen.getByText('73%')).toBeInTheDocument();
  });

  it('renders top implementation cards', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    });

    // "matplotlib" appears in library stats and in top implementation cards
    expect(screen.getAllByText('matplotlib').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('95')).toBeInTheDocument();
  });

  it('renders tag distribution categories', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('plot type')).toBeInTheDocument();
    });

    expect(screen.getByText('data type')).toBeInTheDocument();
    expect(screen.getByText('scatter')).toBeInTheDocument();
  });

  it('renders timeline section', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('timeline')).toBeInTheDocument();
    });
  });

  it('renders visitors section header, chart, and Plausible link when Plausible returns data', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      // 12 + 25 + 7 = 44 total
      expect(screen.getByText(/unique visitors · last 28 days · 44 total/)).toBeInTheDocument();
    });
    // section header matches the libraries/timeline pattern
    expect(screen.getByText('visitors')).toBeInTheDocument();
    // link makes the destination explicit, styled as a code-call to match the
    // site's terminal/monospace aesthetic
    expect(screen.getByText('plausible.view()')).toBeInTheDocument();
  });

  it('renders the "visitor data unavailable" placeholder when Plausible returns empty points', async () => {
    mockFetchSuccess({ points: [] });

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText(/visitor data unavailable/)).toBeInTheDocument();
    });
  });

  it('routes tag links to /plots and fires tag_click on click', async () => {
    // Regression: pre-fix the href pointed at /?plot=scatter, which landed
    // on LandingPage and silently dropped the filter intent. Filter routing
    // lives on /plots after the page split, so the link must target that.
    mockFetchSuccess();
    const user = userEvent.setup();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('scatter')).toBeInTheDocument();
    });

    const scatterLink = screen.getByText('scatter').closest('a');
    expect(scatterLink).toHaveAttribute('href', '/plots?plot=scatter');

    // Tag with a space exercises encodeURIComponent — proves the encoding
    // step isn't a no-op.
    const timeSeriesLink = screen.getByText('time series').closest('a');
    expect(timeSeriesLink).toHaveAttribute('href', '/plots?data=time%20series');

    await user.click(scatterLink!);
    expect(mockTrackEvent).toHaveBeenCalledWith('tag_click', {
      param: 'plot',
      value: 'scatter',
      source: 'stats',
    });

    await user.click(timeSeriesLink!);
    expect(mockTrackEvent).toHaveBeenCalledWith('tag_click', {
      param: 'data',
      value: 'time series',
      source: 'stats',
    });
  });
});
