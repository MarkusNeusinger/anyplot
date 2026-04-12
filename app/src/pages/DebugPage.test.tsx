import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';

vi.mock('../components/Breadcrumb', () => ({
  Breadcrumb: () => <nav data-testid="breadcrumb">Breadcrumb</nav>,
}));

import { DebugPage } from './DebugPage';

const mockDebugData = {
  total_specs: 100,
  total_implementations: 500,
  coverage_percent: 85.5,
  library_stats: [
    { id: 'matplotlib', name: 'Matplotlib', impl_count: 80, avg_score: 91.5, min_score: 60, max_score: 99 },
  ],
  low_score_specs: [],
  oldest_specs: [],
  missing_preview_specs: [],
  missing_tags_specs: [],
  system: {
    database_connected: true,
    api_response_time_ms: 42,
    timestamp: '2025-01-15T10:00:00Z',
    total_specs_in_db: 100,
    total_impls_in_db: 500,
  },
  specs: [
    {
      id: 'scatter-basic',
      title: 'Basic Scatter',
      updated: '2025-01-01',
      avg_score: 92,
      altair: 90, bokeh: 91, highcharts: null, letsplot: null,
      matplotlib: 95, plotly: 88, plotnine: null, pygal: null, seaborn: 94,
    },
  ],
};

describe('DebugPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    render(<DebugPage />);
    // During loading, shows skeletons
    const skeletons = document.querySelectorAll('.MuiSkeleton-root');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders debug data after fetch', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDebugData),
      })
    ));

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText('scatter-basic')).toBeInTheDocument();
    });
  });

  it('handles fetch error gracefully', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: false, status: 500 })
    ));

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('renders breadcrumb after data loads', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDebugData),
      })
    ));
    render(<DebugPage />);
    await waitFor(() => {
      expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
    });
  });
});
