import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SpecPage } from 'src/pages/SpecPage';
import { render, screen, waitFor } from 'src/test-utils';

const mockNavigate = vi.fn();
let mockParams: Record<string, string | undefined> = { specId: 'scatter-basic' };
const mockSearchParams = new URLSearchParams();
const mockSetSearchParams = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => mockParams,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [mockSearchParams, mockSetSearchParams],
  };
});

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// The real useAnalytics returns useCallback-stable functions. Rebuilding them
// per render here would give every consumer a fresh identity, which turns any
// effect that lists trackEvent as a dependency into an infinite render loop —
// so the mock has to hold the same contract.
const mockTrackEvent = vi.fn();
const mockAnalytics = { trackPageview: vi.fn(), trackEvent: mockTrackEvent };

vi.mock('src/hooks', () => ({
  useAnalytics: () => mockAnalytics,
  useAppData: () => ({
    librariesData: [
      { id: 'matplotlib', name: 'Matplotlib', language: 'python' },
      { id: 'seaborn', name: 'Seaborn', language: 'python' },
    ],
  }),
  useCodeFetch: () => ({
    fetchCode: vi.fn().mockResolvedValue(null),
    getCode: vi.fn().mockReturnValue(null),
    isLoading: false,
  }),
}));

// Mock lazy-loaded components as simple divs
vi.mock('src/sections/spec-detail/SpecTabs', () => ({
  SpecTabs: () => <div data-testid="spec-tabs">SpecTabs</div>,
}));

vi.mock('src/sections/spec-detail/SpecOverview', () => ({
  SpecOverview: () => <div data-testid="spec-overview">SpecOverview</div>,
}));

vi.mock('src/sections/spec-detail/SpecDetailView', () => ({
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
      language: 'python',
      preview_url: 'https://example.com/scatter-basic/matplotlib/plot.png',
      quality_score: 8,
      code: null,
    },
    {
      library_id: 'seaborn',
      library_name: 'Seaborn',
      language: 'python',
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
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(data),
  });
}

function mockFetch404() {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: false,
    status: 404,
    json: () => Promise.resolve({}),
  });
}

function mockFetchError() {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
}

describe('SpecPage', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear();
  });

  it('shows loading state initially', () => {
    // Never-resolving fetch keeps loading=true
    globalThis.fetch = vi.fn().mockReturnValue(new Promise(() => {}));
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
      expect(
        screen.getByRole('heading', { level: 1, name: /page not found/i })
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/404 — no route matched/i)).toBeInTheDocument();
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
    mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spec-detail-view')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('spec-overview')).not.toBeInTheDocument();
  });

  it('reports impl_missing when the URL names an implementation that is gone', async () => {
    // The shape a library migration leaves behind: the spec exists, the
    // library/language pair does not. The visitor is redirected to the hub
    // rather than shown a 404, so this event is the only trace it leaves.
    mockParams = { specId: 'scatter-basic', language: 'python', library: 'highcharts' };
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(mockTrackEvent).toHaveBeenCalledWith('page_not_found', {
        path: window.location.pathname,
        source: 'impl_missing',
      });
    });
  });

  it('does not report a miss when the implementation exists', async () => {
    mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spec-detail-view')).toBeInTheDocument();
    });
    expect(mockTrackEvent).not.toHaveBeenCalledWith('page_not_found', expect.anything());
  });

  it('renders description text', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByText('A scatter plot with basic configuration')).toBeInTheDocument();
    });
  });

  it('calls fetch with correct spec endpoint', async () => {
    mockFetchSuccess();
    render(<SpecPage />);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });
    const fetchUrl = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(fetchUrl).toContain('/specs/scatter-basic');
  });

  describe('language in document title', () => {
    it('includes ` · python · matplotlib` in the document title in detail mode', async () => {
      mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
      mockSearchParams.delete('language');
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() => {
        expect(document.title).toContain('Basic Scatter Plot · python · matplotlib');
      });
    });

    it('includes ` · python` in the document title when ?language= is set in hub mode', async () => {
      mockParams = { specId: 'scatter-basic' };
      mockSearchParams.set('language', 'python');
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() => {
        expect(document.title).toContain('Basic Scatter Plot · python');
      });
      mockSearchParams.delete('language');
    });

    it('lowercases a mixed-case path language token in detail mode', async () => {
      mockParams = { specId: 'scatter-basic', language: 'Python', library: 'matplotlib' };
      mockSearchParams.delete('language');
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() => {
        expect(document.title).toContain('Basic Scatter Plot · python · matplotlib');
      });
      expect(document.title).not.toContain('Python');
    });

    it('lowercases a mixed-case ?language= query param in hub mode', async () => {
      mockParams = { specId: 'scatter-basic' };
      mockSearchParams.set('language', 'Python');
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() => {
        expect(document.title).toContain('Basic Scatter Plot · python');
      });
      expect(document.title).not.toContain('Python');
      mockSearchParams.delete('language');
    });
  });

  describe('carousel-scope conflict drop', () => {
    it('drops ?language= when it conflicts with the URL path language in detail mode', async () => {
      // Spec has both a python/matplotlib and a python/seaborn impl. We put
      // ?language=r on the URL so the carousel scope (r) conflicts with the
      // path language (python) — the effect should call setSearchParams to
      // strip the query.
      mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
      mockSearchParams.set('language', 'r');
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() => {
        expect(mockSetSearchParams).toHaveBeenCalled();
      });
      // The drop call passes a URLSearchParams with no `language` key.
      const calls = mockSetSearchParams.mock.calls;
      const lastCall = calls[calls.length - 1];
      const params = lastCall?.[0] as URLSearchParams;
      expect(params.get('language')).toBeNull();
      mockSearchParams.delete('language');
    });

    it('does not drop ?language= when it matches the URL path language', async () => {
      mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
      mockSearchParams.set('language', 'python');
      mockSetSearchParams.mockClear();
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() => {
        expect(screen.getByTestId('spec-detail-view')).toBeInTheDocument();
      });
      // No drop call — the languages agree.
      expect(mockSetSearchParams).not.toHaveBeenCalled();
      mockSearchParams.delete('language');
    });
  });
});
