import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { StatsPage } from './StatsPage';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: vi.fn(),
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
      quality_score: 95,
      preview_url: 'https://example.com/img.png',
    },
  ],
  tag_distribution: {
    plot_type: { scatter: 42, line: 30 },
    data_type: { numeric: 80 },
  },
  score_distribution: { '50-60': 5, '60-70': 10, '70-80': 20, '80-90': 30, '90-100': 15 },
  timeline: [
    { month: '2025-01', count: 10 },
    { month: '2025-02', count: 20 },
  ],
};

function mockFetchSuccess() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboard),
    }),
  );
}

function mockFetchError() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    }),
  );
}

describe('StatsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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
    // avg_quality_score: 82.5 => formatNum(82.5) => "82.5" (toLocaleString)
    expect(screen.getByText('82.5')).toBeInTheDocument();
    // coverage_percent: 73 => "73%"
    expect(screen.getByText('73%')).toBeInTheDocument();
  });

  it('renders breadcrumb navigation', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: 'breadcrumb' })).toBeInTheDocument();
    });
  });

  it('renders footer with github link', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('github')).toBeInTheDocument();
    });
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
});
