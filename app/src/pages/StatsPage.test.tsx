import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeContext, type ThemeContextValue } from 'src/hooks/useLayoutContext';
import { StatsPage } from 'src/pages/StatsPage';
import { render, screen, userEvent, waitFor, within } from 'src/test-utils';

const darkThemeValue: ThemeContextValue = {
  mode: 'dark',
  effective: 'dark',
  isDark: true,
  setMode: vi.fn(),
  cycle: vi.fn(),
};

const mockTrackEvent = vi.fn();

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

// Mirrors core.constants.SUPPORTED_LIBRARIES (15 entries).
const ALL_LIBRARY_IDS = [
  'altair',
  'bokeh',
  'chartjs',
  'd3',
  'echarts',
  'ggplot2',
  'highcharts',
  'letsplot',
  'makie',
  'matplotlib',
  'muix',
  'plotly',
  'plotnine',
  'pygal',
  'seaborn',
];

const mockDashboard = {
  total_specs: 142,
  total_implementations: 987,
  total_interactive: 53,
  total_lines_of_code: 245_600,
  avg_quality_score: 82.5,
  coverage_percent: 73,
  // Denominator of the coverage matrix — served by the API, never hardcoded
  // in the page (it used to be a stale literal 9).
  total_libraries: 15,
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
    // echarts/muix carry their canonical API names so the StatsPage short-label
    // override (statsLibLabel) is exercised: 'Apache ECharts' -> 'ECharts',
    // 'MUI X Charts' -> 'MUI X'. matplotlib above asserts the fallback to name.
    {
      id: 'echarts',
      name: 'Apache ECharts',
      impl_count: 30,
      avg_score: 89,
      min_score: 70,
      max_score: 96,
      score_buckets: { '85-90': 5, '90-95': 8 },
      loc_buckets: { '60-80': 4 },
      avg_loc: 95,
    },
    {
      id: 'muix',
      name: 'MUI X Charts',
      impl_count: 8,
      avg_score: 88,
      min_score: 72,
      max_score: 94,
      score_buckets: { '85-90': 3, '90-95': 2 },
      loc_buckets: { '80-100': 2 },
      avg_loc: 110,
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
    // A fully covered spec — 15/15, the state the matrix renders as solid green.
    {
      spec_id: 'line-basic',
      title: 'Basic Line Plot',
      libraries: Object.fromEntries(ALL_LIBRARY_IDS.map(id => [id, { score: 90, has_impl: true }])),
    },
  ],
  top_implementations: [
    {
      spec_id: 'scatter-basic',
      spec_title: 'Basic Scatter Plot',
      library_id: 'matplotlib',
      language: 'python',
      quality_score: 95,
      preview_url: 'https://example.com/img-light.png',
      preview_url_light: 'https://example.com/img-light.png',
      preview_url_dark: 'https://example.com/img-dark.png',
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

/** 28 UTC days, oldest first, every one zero but the two given. */
function machineReaderDays(
  overrides: Record<
    string,
    Partial<Record<'for_person' | 'index_training' | 'search' | 'mcp', number>>
  >
) {
  return Array.from({ length: 28 }, (_, offset) => {
    const date = new Date(Date.UTC(2026, 9, 13 + offset)).toISOString().slice(0, 10);
    return { date, for_person: 0, index_training: 0, search: 0, mcp: 0, ...overrides[date] };
  });
}

const mockMachineReaders = {
  status: 'ok',
  days: 28,
  points: machineReaderDays({
    '2026-10-20': { index_training: 1 },
    '2026-11-09': { for_person: 2, index_training: 16, search: 3, mcp: 4 },
  }),
  totals: { for_person: 2, index_training: 17, search: 3, mcp: 4, unverified: 26 },
  generated_at: '2026-11-09T13:50:00Z',
};

/**
 * StatsPage performs three independent fetches: /insights/dashboard,
 * /insights/visitors and /insights/machine-readers. Route by URL so no
 * response is silently replaced by the dashboard payload (and vice versa).
 * A `null` machine readers payload answers 403, a non-retryable status.
 */
function mockFetchSuccess(
  visitorsPayload: { points: Array<{ date: string; visitors: number }> } | null = mockVisitors,
  machineReadersPayload: unknown = mockMachineReaders
) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      if (url.includes('/insights/visitors')) {
        return Promise.resolve({
          ok: visitorsPayload !== null,
          json: () => Promise.resolve(visitorsPayload ?? { points: [] }),
        });
      }
      if (url.includes('/insights/machine-readers')) {
        return Promise.resolve(
          machineReadersPayload === null
            ? { ok: false, status: 403 }
            : { ok: true, json: () => Promise.resolve(machineReadersPayload) }
        );
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDashboard),
      });
    })
  );
}

function mockFetchError() {
  // /insights/dashboard fails; visitors and machine readers can succeed so
  // their `useEffect`s resolve cleanly and the test asserts on the dashboard
  // error path only.
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      if (url.includes('/insights/visitors')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ points: [] }) });
      }
      if (url.includes('/insights/machine-readers')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(mockMachineReaders) });
      }
      // A non-retryable status: apiGet would retry a 5xx with real backoff
      // (covered in lib/api.test.ts), outlasting waitFor's 1 s default.
      return Promise.resolve({ ok: false, status: 403 });
    })
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

  it('scales the coverage matrix by total_libraries, not a hardcoded count', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('specifications')).toBeInTheDocument();
    });

    // total_specs (142) * total_libraries (15) = 2130 possible implementations,
    // and one of the two matrix rows is short of full coverage.
    expect(screen.getByText(/987 of 2,?130 possible/)).toBeInTheDocument();
    expect(screen.getByText(/1 below 15\/15/)).toBeInTheDocument();
    expect(screen.getByText('complete (15/15)')).toBeInTheDocument();
  });

  it('labels each coverage cell with its count out of the full library set', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Basic Scatter Plot: 1/15')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Basic Line Plot: 15/15')).toBeInTheDocument();
  });

  it('falls back to library_stats when an older payload omits total_libraries', async () => {
    // Frontend-before-API deploy: the cached/older dashboard has no
    // total_libraries, so the denominator has to come from library_stats.
    const legacyDashboard: Record<string, unknown> = {
      ...mockDashboard,
      library_stats: ALL_LIBRARY_IDS.map(id => ({
        id,
        name: id,
        impl_count: 10,
        avg_score: 85,
        min_score: 60,
        max_score: 98,
        score_buckets: { '85-90': 5 },
        loc_buckets: { '40-60': 5 },
        avg_loc: 78,
      })),
    };
    delete legacyDashboard.total_libraries;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('/insights/visitors')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ points: [] }) });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(legacyDashboard) });
      })
    );

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Basic Scatter Plot: 1/15')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Basic Line Plot: 15/15')).toBeInTheDocument();
    expect(screen.getByText(/987 of 2,?130 possible/)).toBeInTheDocument();
    expect(screen.getByText(/1 below 15\/15/)).toBeInTheDocument();
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

  it('shows the theme-matching top-rated thumbnail in light and in dark mode', async () => {
    mockFetchSuccess();

    const { unmount } = render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    });
    expect(screen.getByAltText('Basic Scatter Plot')).toHaveAttribute(
      'src',
      'https://example.com/img-light_800.png'
    );
    unmount();

    mockFetchSuccess();
    render(
      <ThemeContext.Provider value={darkThemeValue}>
        <StatsPage />
      </ThemeContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    });
    expect(screen.getByAltText('Basic Scatter Plot')).toHaveAttribute(
      'src',
      'https://example.com/img-dark_800.png'
    );
  });

  it('shortens echarts/muix library labels and falls back to name for others', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('libraries')).toBeInTheDocument();
    });

    // statsLibLabel maps the canonical API names to single-line labels. Each
    // appears twice — once in the quality histogram, once in the LOC histogram.
    expect(screen.getAllByText('ECharts')).toHaveLength(2);
    expect(screen.getAllByText('MUI X')).toHaveLength(2);
    // The canonical names must NOT leak through anywhere on the page.
    expect(screen.queryByText('Apache ECharts')).not.toBeInTheDocument();
    expect(screen.queryByText('MUI X Charts')).not.toBeInTheDocument();
    // Libraries without an override still render their plain name (2 histograms).
    expect(screen.getAllByText('matplotlib').length).toBeGreaterThanOrEqual(2);
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

  it('renders the machine readers tile: header, total, legend, footnote and 28 days', async () => {
    mockFetchSuccess();

    render(<StatsPage />);

    // 2 + 17 + 3: the three audiences, the MCP requests apart.
    await waitFor(() => {
      expect(
        screen.getByText(/verified crawlers and ai assistants · last 28 days · 22 requests/)
      ).toBeInTheDocument();
    });
    expect(screen.getByText('machine readers')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'legal.privacy()' })).toHaveAttribute(
      'href',
      '/legal#machine-readers'
    );
    const legend = screen.getByTestId('machine-readers-legend');
    expect(legend).toHaveTextContent('for a person 2');
    expect(legend).toHaveTextContent('ai index & training 17');
    expect(legend).toHaveTextContent('search engines 3');
    expect(legend).toHaveTextContent('· 4 over mcp (all clients)');
    const footnote = screen.getByTestId('machine-readers-footnote');
    expect(footnote).toHaveTextContent('requests that reached the server');
    expect(footnote).toHaveTextContent('people are counted in visitors above');
    expect(footnote).toHaveTextContent(
      "26 requests that carried a crawler's name without that verification are not counted."
    );
    expect(footnote).not.toHaveTextContent(/spoof/);

    const days = screen.getAllByTestId('machine-readers-day');
    expect(days).toHaveLength(28);
    expect(days[27]).toHaveAttribute(
      'aria-label',
      '2026-11-09: 21 requests · 2 for a person · 16 ai index & training · 3 search engines'
    );
    expect(days[7]).toHaveAttribute(
      'aria-label',
      '2026-10-20: 1 request · 0 for a person · 1 ai index & training · 0 search engines'
    );
    // Each day is a named, focusable image, so a keyboard and a screen reader reach its numbers.
    const strip = screen.getByRole('group', { name: 'machine readers per day' });
    expect(
      within(strip).getByRole('img', {
        name: '2026-11-09: 21 requests · 2 for a person · 16 ai index & training · 3 search engines',
      })
    ).toHaveAttribute('tabindex', '0');
    expect(within(strip).getAllByRole('img')).toHaveLength(28);
  });

  it.each([
    ['unavailable', { ...mockMachineReaders, status: 'unavailable', points: [] }],
    ['not_configured', { ...mockMachineReaders, status: 'not_configured', points: [] }],
    ['an unreadable answer', { status: 'ok', points: 'nope' }],
  ])('shows the machine readers placeholder for %s', async (_, payload) => {
    mockFetchSuccess(mockVisitors, payload);

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('machine reader data unavailable')).toBeInTheDocument();
    });
    expect(
      screen.getByText(/verified crawlers and ai assistants · last 28 days$/)
    ).toBeInTheDocument();
    expect(screen.queryByTestId('machine-readers-day')).not.toBeInTheDocument();
  });

  it('draws 28 honest minimum bars for an ok answer with no reads', async () => {
    mockFetchSuccess(mockVisitors, {
      ...mockMachineReaders,
      points: machineReaderDays({}),
      totals: { for_person: 0, index_training: 0, search: 0, mcp: 0, unverified: 0 },
    });

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getAllByTestId('machine-readers-day')).toHaveLength(28);
    });
    expect(screen.getByText(/last 28 days · 0 requests/)).toBeInTheDocument();
    expect(screen.getByTestId('machine-readers-legend')).toHaveTextContent(
      '· 0 over mcp (all clients)'
    );
  });

  it('still renders the dashboard when the machine readers request fails', async () => {
    mockFetchSuccess(mockVisitors, null);

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByText('machine reader data unavailable')).toBeInTheDocument();
    });
    expect(screen.getByText('specifications')).toBeInTheDocument();
    expect(screen.getByText(/unique visitors · last 28 days · 44 total/)).toBeInTheDocument();
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
