import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { CatalogPage } from './CatalogPage';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: vi.fn(),
  }),
  useAppData: () => ({
    specsData: [
      { id: 'bar-basic', title: 'Basic Bar Chart', description: 'A simple bar chart' },
      { id: 'scatter-basic', title: 'Basic Scatter Plot', description: 'A scatter plot' },
    ],
  }),
  useHomeState: () => ({
    saveScrollPosition: vi.fn(),
  }),
}));

vi.mock('../utils/responsiveImage', () => ({
  buildSrcSet: (url: string, _format: string) => url,
  getFallbackSrc: (url: string) => url,
  CATALOG_SIZES: '280px',
}));

const mockImages = {
  images: [
    { library: 'matplotlib', url: 'https://example.com/bar-basic/matplotlib/plot.png', spec_id: 'bar-basic' },
    { library: 'seaborn', url: 'https://example.com/bar-basic/seaborn/plot.png', spec_id: 'bar-basic' },
    { library: 'matplotlib', url: 'https://example.com/scatter-basic/matplotlib/plot.png', spec_id: 'scatter-basic' },
  ],
};

beforeEach(() => {
  vi.restoreAllMocks();
});

function mockFetchSuccess() {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(mockImages),
  });
}

function mockFetchError() {
  global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
}

describe('CatalogPage', () => {
  it('shows loading state initially', () => {
    // Never-resolving fetch keeps loading=true
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {}));
    render(<CatalogPage />);

    // Loading state renders Skeleton placeholders (MUI Skeleton uses role="progressbar" internally, but we can check for the skeleton structure)
    // The loading branch renders multiple Skeleton elements; heading text should NOT be present
    expect(screen.queryByText('catalog')).not.toBeInTheDocument();
  });

  it('renders specs after successful fetch', async () => {
    mockFetchSuccess();
    render(<CatalogPage />);

    await waitFor(() => {
      expect(screen.getByText('Basic Bar Chart')).toBeInTheDocument();
    });
    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    expect(screen.getByText('A simple bar chart')).toBeInTheDocument();
    expect(screen.getByText('A scatter plot')).toBeInTheDocument();
  });

  it('handles fetch error gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetchError();
    render(<CatalogPage />);

    // After error, loading ends and we get the catalog heading (with 0 specs matched since no images loaded)
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });
    expect(screen.getByText('0 specifications')).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  it('renders breadcrumb navigation', async () => {
    mockFetchSuccess();
    render(<CatalogPage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });
    expect(screen.getByRole('navigation', { name: 'breadcrumb' })).toBeInTheDocument();
  });

  it('renders footer', async () => {
    mockFetchSuccess();
    render(<CatalogPage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });
    expect(screen.getByText('github')).toBeInTheDocument();
  });

  it('has page title text', async () => {
    mockFetchSuccess();
    render(<CatalogPage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('catalog');
  });

  it('shows specification count', async () => {
    mockFetchSuccess();
    render(<CatalogPage />);

    await waitFor(() => {
      expect(screen.getByText('2 specifications')).toBeInTheDocument();
    });
  });

  it('calls fetch with /plots/filter endpoint', async () => {
    mockFetchSuccess();
    render(<CatalogPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    const fetchUrl = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(fetchUrl).toContain('/plots/filter');
  });
});
