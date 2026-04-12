import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { SpecPage } from './SpecPage';

const mockNavigate = vi.fn();
let mockParams: Record<string, string | undefined> = { specId: 'scatter-basic' };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => mockParams,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: vi.fn(),
  }),
  useAppData: () => ({
    librariesData: [
      { id: 'matplotlib', name: 'Matplotlib' },
      { id: 'seaborn', name: 'Seaborn' },
    ],
  }),
  useCodeFetch: () => ({
    fetchCode: vi.fn().mockResolvedValue(null),
    getCode: vi.fn().mockReturnValue(null),
    isLoading: false,
  }),
}));

// Mock lazy-loaded components as simple divs
vi.mock('../components/SpecTabs', () => ({
  SpecTabs: () => <div data-testid="spec-tabs">SpecTabs</div>,
}));

vi.mock('../components/SpecOverview', () => ({
  SpecOverview: () => <div data-testid="spec-overview">SpecOverview</div>,
}));

vi.mock('../components/SpecDetailView', () => ({
  SpecDetailView: () => <div data-testid="spec-detail-view">SpecDetailView</div>,
}));

const mockSpecData = {
  id: 'scatter-basic',
  title: 'Basic Scatter Plot',
  description: 'A scatter plot with basic configuration',
  implementations: [
    {
      library_id: 'matplotlib',
      library_name: 'Matplotlib',
      preview_url: 'https://example.com/scatter-basic/matplotlib/plot.png',
      quality_score: 8,
      code: null,
    },
    {
      library_id: 'seaborn',
      library_name: 'Seaborn',
      preview_url: 'https://example.com/scatter-basic/seaborn/plot.png',
      quality_score: 7,
      code: null,
    },
  ],
};

beforeEach(() => {
  vi.restoreAllMocks();
  mockParams = { specId: 'scatter-basic' };
  mockNavigate.mockReset();
});

function mockFetchSuccess(data = mockSpecData) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(data),
  });
}

function mockFetch404() {
  global.fetch = vi.fn().mockResolvedValue({
    ok: false,
    status: 404,
    json: () => Promise.resolve({}),
  });
}

function mockFetchError() {
  global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
}

describe('SpecPage', () => {
  it('shows loading state initially', () => {
    // Never-resolving fetch keeps loading=true
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {}));
    render(<SpecPage />);

    // Loading state does NOT show the spec title
    expect(screen.queryByText('Basic Scatter Plot')).not.toBeInTheDocument();
  });

  it('renders spec title after fetch', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Basic Scatter Plot');
    });
  });

  it('shows 404 page when spec not found', async () => {
    mockFetch404();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByText('404')).toBeInTheDocument();
    });
    expect(screen.getByText('page not found')).toBeInTheDocument();
  });

  it('handles fetch error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetchError();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load spec')).toBeInTheDocument();
    });
    consoleSpy.mockRestore();
  });

  it('renders breadcrumb with spec id', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: 'breadcrumb' })).toBeInTheDocument();
    });
    // Breadcrumb should contain the spec id
    expect(screen.getByText('scatter-basic')).toBeInTheDocument();
  });

  it('renders overview mode when no library in URL params', async () => {
    mockParams = { specId: 'scatter-basic' };
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spec-overview')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('spec-detail-view')).not.toBeInTheDocument();
  });

  it('renders detail mode when library in URL params', async () => {
    mockParams = { specId: 'scatter-basic', library: 'matplotlib' };
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spec-detail-view')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('spec-overview')).not.toBeInTheDocument();
  });

  it('renders description text', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByText('A scatter plot with basic configuration')).toBeInTheDocument();
    });
  });

  it('renders footer', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByText('github')).toBeInTheDocument();
    });
  });

  it('calls fetch with correct spec endpoint', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    const fetchUrl = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(fetchUrl).toContain('/specs/scatter-basic');
  });
});
