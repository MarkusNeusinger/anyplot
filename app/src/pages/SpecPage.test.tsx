import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SpecPage } from 'src/pages/SpecPage';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

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

// The real useAnalytics returns useCallback-stable functions. Rebuilding them
// per render here would give every consumer a fresh identity, which turns any
// effect that lists trackEvent as a dependency into an infinite render loop —
// so the mock has to hold the same contract.
const mockTrackEvent = vi.fn();
const mockAnalytics = { trackEvent: mockTrackEvent };

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

// Mock lazy-loaded components as simple divs; SpecTabs exposes the date it is handed and
// whether it got the chat's entry for the code tab
vi.mock('src/sections/spec-detail/SpecTabs', () => ({
  SpecTabs: ({ updated, onUseWithMyData }: { updated?: string; onUseWithMyData?: () => void }) => (
    <div
      data-testid="spec-tabs"
      data-updated={updated ?? ''}
      data-use-my-data={onUseWithMyData ? 'yes' : 'no'}
    >
      SpecTabs
    </div>
  ),
}));

vi.mock('src/sections/spec-detail/SpecOverview', () => ({
  SpecOverview: () => <div data-testid="spec-overview">SpecOverview</div>,
}));

vi.mock('src/sections/spec-detail/SpecDetailView', () => ({
  SpecDetailView: () => <div data-testid="spec-detail-view">SpecDetailView</div>,
}));

// The lane `useAgentEligibility` names for the pair; null is no entry (also while it probes).
// `asked` records the pairs the page asks about, one per render.
const agentEligibility: {
  lane: 'admin' | 'public' | null;
  asked: [string | null | undefined, string | null | undefined][];
} = { lane: null, asked: [] };
vi.mock('src/hooks/useAgentEligibility', () => ({
  useAgentEligibility: (spec: string | null | undefined, library: string | null | undefined) => {
    agentEligibility.asked.push([spec, library]);
    return agentEligibility.lane;
  },
}));
/** The libraries the page asked the eligibility about, each once. */
const askedLibraries = () => [
  ...new Set(agentEligibility.asked.map(([, library]) => library).filter(Boolean)),
];

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
  agentEligibility.lane = null;
  agentEligibility.asked = [];
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

  it('offers .retry() on a failed load and recovers in place on click', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetchError();
    render(<SpecPage />);

    const retry = await screen.findByRole('button', { name: 'Retry loading the spec' });
    expect(retry).toHaveTextContent('.retry()');

    mockFetchSuccess();
    await userEvent.click(retry);

    expect(await screen.findByText('Basic Scatter Plot')).toBeInTheDocument();
    expect(screen.queryByText('Failed to load spec')).not.toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  it('does not offer .retry() for a missing spec', async () => {
    mockFetch404();
    render(<SpecPage />);

    await waitFor(() => {
      expect(screen.getByText(/404 — no route matched/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: 'Retry loading the spec' })).toBeNull();
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

  it("hands the implementation's own update date to the tabs in detail mode, not the spec's", async () => {
    mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
    mockFetchSuccess({
      ...mockSpecData,
      updated: '2025-12-23T00:22:47',
      implementations: mockSpecData.implementations.map(impl =>
        impl.library_id === 'matplotlib'
          ? { ...impl, generated_at: '2025-12-23T00:22:47', updated: '2026-11-01T02:33:45' }
          : impl
      ),
    } as typeof mockSpecData);
    render(<SpecPage />);

    expect(await screen.findByTestId('spec-tabs')).toHaveAttribute(
      'data-updated',
      '2026-11-01T02:33:45'
    );
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

  it('puts .use_my_data() beside the carousel only for an eligible pair', async () => {
    mockParams = { specId: 'scatter-basic', language: 'python', library: 'matplotlib' };
    mockFetchSuccess();
    const { rerender } = render(<SpecPage />);

    await screen.findByRole('button', { name: 'Back to library comparison' });
    expect(screen.queryByRole('button', { name: 'Use with my data' })).not.toBeInTheDocument();

    agentEligibility.lane = 'public';
    rerender(<SpecPage />);
    await userEvent.click(await screen.findByRole('button', { name: 'Use with my data' }));
    expect(mockNavigate).toHaveBeenCalledWith(
      '/agent?spec=scatter-basic&library=matplotlib&language=python&source=plot_page'
    );
    // The code tab gets the same entry beside its copy button, from the same answer.
    expect(screen.getByTestId('spec-tabs')).toHaveAttribute('data-use-my-data', 'yes');
    expect(askedLibraries()).toEqual(['matplotlib']);
  });

  it('gives the code tab no entry for a pair that is not eligible', async () => {
    mockParams = { specId: 'scatter-basic', language: 'python', library: 'seaborn' };
    mockFetchSuccess();
    render(<SpecPage />);

    expect(await screen.findByTestId('spec-tabs')).toHaveAttribute('data-use-my-data', 'no');
  });

  it("puts .use_my_data() in the hub's header, asking about matplotlib only", async () => {
    mockParams = { specId: 'scatter-basic' };
    agentEligibility.lane = 'public';
    mockFetchSuccess({
      ...mockSpecData,
      // matplotlib second: the hub still asks about it, not about the first card.
      implementations: [...mockSpecData.implementations].reverse(),
    });
    render(<SpecPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Use with my data' }));
    expect(mockNavigate).toHaveBeenCalledWith(
      '/agent?spec=scatter-basic&library=matplotlib&language=python&source=spec_hub'
    );
    // One library for the whole hub, never one per card.
    expect(askedLibraries()).toEqual(['matplotlib']);
    expect(screen.getAllByRole('button', { name: 'Use with my data' })).toHaveLength(1);
  });

  it('asks about the first card on a hub without matplotlib, in the order of the cards', async () => {
    mockParams = { specId: 'scatter-basic' };
    agentEligibility.lane = 'public';
    mockFetchSuccess({
      ...mockSpecData,
      // The API's order is seaborn, bokeh; the cards are sorted by library id, bokeh first.
      implementations: [
        ...mockSpecData.implementations.filter(impl => impl.library_id !== 'matplotlib'),
        {
          library_id: 'bokeh',
          library_name: 'Bokeh',
          language: 'python',
          preview_url: 'https://example.com/scatter-basic/bokeh/plot.png',
          quality_score: 8,
          code: null,
        },
      ],
    });
    render(<SpecPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Use with my data' }));
    expect(mockNavigate).toHaveBeenCalledWith(
      '/agent?spec=scatter-basic&library=bokeh&language=python&source=spec_hub'
    );
    expect(askedLibraries()).toEqual(['bokeh']);
  });

  it('asks about a library of the shown language on a hub under ?language=', async () => {
    mockParams = { specId: 'scatter-basic' };
    mockSearchParams.set('language', 'r');
    agentEligibility.lane = 'public';
    mockFetchSuccess({
      ...mockSpecData,
      implementations: [
        ...mockSpecData.implementations,
        {
          library_id: 'ggplot2',
          library_name: 'ggplot2',
          language: 'r',
          preview_url: 'https://example.com/scatter-basic/ggplot2/plot.png',
          quality_score: 9,
          code: null,
        },
      ],
    });
    render(<SpecPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Use with my data' }));
    expect(mockNavigate).toHaveBeenCalledWith(
      '/agent?spec=scatter-basic&library=ggplot2&language=r&source=spec_hub'
    );
    // The R cards' library only: matplotlib, not among them, is never asked about.
    expect(askedLibraries()).toEqual(['ggplot2']);
    mockSearchParams.delete('language');
  });

  it('shows no entry on the hub while the eligibility names no lane', async () => {
    mockParams = { specId: 'scatter-basic' };
    mockFetchSuccess();
    render(<SpecPage />);

    await screen.findByTestId('spec-overview');
    expect(screen.queryByRole('button', { name: 'Use with my data' })).not.toBeInTheDocument();
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

  describe('structured data', () => {
    const juliaSpec = {
      ...mockSpecData,
      implementations: [
        {
          library_id: 'makie',
          library_name: 'Makie.jl',
          language: 'julia',
          preview_url: 'https://example.com/scatter-basic/makie/plot.png',
          quality_score: 88,
          code: null,
        },
      ],
    };

    /** The JSON-LD blocks the page renders, by their @type. */
    function jsonLd(): Record<string, Record<string, unknown>> {
      const blocks = Array.from(
        document.querySelectorAll('script[type="application/ld+json"]'),
        s => JSON.parse(s.textContent ?? '{}') as Record<string, unknown>
      );
      return Object.fromEntries(blocks.map(b => [String(b['@type']), b]));
    }

    it('names the language of a Julia implementation with its display name', async () => {
      mockParams = { specId: 'scatter-basic', language: 'julia', library: 'makie' };
      mockSearchParams.delete('language');
      mockFetchSuccess(juliaSpec);
      render(<SpecPage />);

      await waitFor(() => expect(jsonLd().SoftwareSourceCode).toBeDefined());
      expect(jsonLd().SoftwareSourceCode.programmingLanguage).toBe('Julia');
    });

    it('builds the breadcrumb the bot HTML carries: home, spec, library', async () => {
      mockParams = { specId: 'scatter-basic', language: 'julia', library: 'makie' };
      mockSearchParams.delete('language');
      mockFetchSuccess(juliaSpec);
      render(<SpecPage />);

      await waitFor(() => expect(jsonLd().BreadcrumbList).toBeDefined());
      const items = jsonLd().BreadcrumbList.itemListElement as { name: string; item: string }[];
      expect(items.map(i => [i.name, i.item])).toEqual([
        ['anyplot.ai', 'https://anyplot.ai/'],
        ['Basic Scatter Plot', 'https://anyplot.ai/scatter-basic'],
        ['Makie.jl', 'https://anyplot.ai/scatter-basic/julia/makie'],
      ]);
    });

    it('shares the spec card as og:image on the hub', async () => {
      mockParams = { specId: 'scatter-basic' };
      mockSearchParams.delete('language');
      mockFetchSuccess();
      render(<SpecPage />);

      await waitFor(() =>
        expect(document.head.querySelector('meta[property="og:image"]')).toHaveAttribute(
          'content',
          'https://api.anyplot.ai/og/scatter-basic.png'
        )
      );
    });

    it('shares the home card on the hub of a spec with no render, like the bot HTML', async () => {
      mockParams = { specId: 'scatter-basic' };
      mockSearchParams.delete('language');
      mockFetchSuccess({
        ...mockSpecData,
        implementations: mockSpecData.implementations.map(impl => ({ ...impl, preview_url: '' })),
      });
      render(<SpecPage />);

      await waitFor(() =>
        expect(document.head.querySelector('meta[property="og:image"]')).toHaveAttribute(
          'content',
          'https://api.anyplot.ai/og/home.png'
        )
      );
    });
  });
});
