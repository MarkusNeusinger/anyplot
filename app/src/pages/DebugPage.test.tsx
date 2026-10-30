import { fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { DebugPage } from 'src/pages/DebugPage';
import { render, screen, waitFor, within } from 'src/test-utils';

const mockDebugData = {
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
      altair: 90,
      bokeh: 91,
      chartjs: null,
      d3: null,
      echarts: null,
      ggplot2: null,
      highcharts: null,
      letsplot: null,
      makie: null,
      matplotlib: 95,
      muix: 87,
      plotly: 88,
      plotnine: null,
      pygal: null,
      seaborn: 94,
    },
  ],
};

describe('DebugPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {}))
    );
    render(<DebugPage />);
    expect(screen.getByText(/loading debug data/i)).toBeInTheDocument();
  });

  it('renders debug data after fetch', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) => {
        if (url.includes('/debug/ping')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                database_connected: true,
                response_time_ms: 42,
                timestamp: '2026-04-24T12:00:00Z',
              }),
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDebugData) });
      })
    );

    localStorage.removeItem('anyplot.adminHint');
    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getAllByText('scatter-basic').length).toBeGreaterThan(0);
    });
    // A 200 from /debug/status marks this browser as an admin's, which lets
    // the plot page show the agent chat's `.adapt()` button.
    expect(localStorage.getItem('anyplot.adminHint')).toBe('1');
  });

  it('renders the agent cases section after /debug/status', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/debug/agent/cases')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              items: [
                {
                  id: '20261012T143005Z-1a2b3c4d',
                  created_at: '2026-10-12T14:30:05Z',
                  reaction: 'bug',
                  message: 'the legend hides points',
                  include_data: true,
                  status: 'new',
                  tags: [],
                  spec_id: 'scatter-basic',
                  library_id: 'seaborn',
                  locale: 'en',
                  result_version: 1,
                  replaces: null,
                  superseded_by: null,
                  promoted_at: null,
                  expected: null,
                  model: null,
                  model_version: null,
                  judge_model: null,
                  prompt_hash: null,
                  pipeline_status: 'ok',
                  attempts: 1,
                  tokens: null,
                  cost_estimate: null,
                  files: ['plot-light.png', 'manifest.json'],
                  user_hash: 'adm_0123456789abcdef',
                  session_hash: '0123456789abcdef',
                  case_uri: 'gs://anyplot-agent-cases/cases/20261012T143005Z-1a2b3c4d/',
                  manifest_schema: 1,
                  updated_at: '2026-10-12T14:30:05Z',
                },
              ],
              has_more: false,
            }),
        });
      }
      if (url.includes('/debug/feedback/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDebugData) });
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<DebugPage />);

    expect(await screen.findByText('agent cases')).toBeInTheDocument();
    expect(await screen.findByText('scatter-basic · seaborn · v1')).toBeInTheDocument();
    // The section asks for the open queue only once the page has loaded.
    const urls = fetchMock.mock.calls.map(call => call[0]);
    const statusAt = urls.findIndex(url => url.includes('/debug/status'));
    const casesAt = urls.findIndex(url => url.includes('/debug/agent/cases'));
    expect(statusAt).toBeGreaterThanOrEqual(0);
    expect(casesAt).toBeGreaterThan(statusAt);
    expect(urls[casesAt]).toMatch(/\/debug\/agent\/cases\?status=open$/);
  });

  it('handles fetch error gracefully', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) => {
        if (url.includes('/debug/ping')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({ database_connected: false, response_time_ms: 0, timestamp: '' }),
          });
        }
        return Promise.resolve({ ok: false, status: 500 });
      })
    );

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  // /debug routes are gated by `require_admin` (api/routers/debug.py). The
  // browser handles the gate via an X-Admin-Token sessionStorage UX; these
  // tests cover the 401/503 branch + submit/clear flow that the existing
  // tests miss (and the codecov/patch gate flagged at 65% diff coverage).
  it('renders the admin-token form on 401', async () => {
    sessionStorage.clear();
    localStorage.setItem('anyplot.adminHint', '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 401 }))
    );

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Admin token (fallback)')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /unlock/i })).toBeInTheDocument();
    expect(screen.getByText(/admin token required/i)).toBeInTheDocument();
    // A refusal clears the admin hint again.
    expect(localStorage.getItem('anyplot.adminHint')).toBeNull();
  });

  it('renders the admin-token form on 503 with the not-configured hint', async () => {
    sessionStorage.clear();
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 503 }))
    );

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText(/admin auth not configured/i)).toBeInTheDocument();
    });
  });

  it('surfaces the server message on 403 (Cloudflare Access denial)', async () => {
    // Cloudflare Access path: signed-in Google account not on the
    // admin_allowed_emails allow-list. Backend returns 403 with the email
    // in the detail; the page should switch to the auth-required screen and
    // show that message instead of falling through to "failed to load: 403".
    sessionStorage.clear();
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 403,
          json: () =>
            Promise.resolve({
              status: 403,
              message: 'User stranger@example.com not authorized',
              path: '/debug/status',
            }),
        })
      )
    );

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText(/stranger@example\.com not authorized/i)).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText('Admin token (fallback)')).toBeInTheDocument();
  });

  it('submits the token, sends X-Admin-Token, and persists to sessionStorage', async () => {
    sessionStorage.clear();
    let callIndex = 0;
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      callIndex += 1;
      // First /debug/status → 401 (no token yet); subsequent calls → ok.
      if (url.includes('/debug/ping')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              database_connected: true,
              response_time_ms: 10,
              timestamp: '2026-04-27T00:00:00Z',
            }),
        });
      }
      if (callIndex === 1) {
        return Promise.resolve({ ok: false, status: 401 });
      }
      // Verify the header is sent on the retry.
      const hdr = (init?.headers as Record<string, string> | undefined)?.['X-Admin-Token'];
      if (hdr !== 'secret-xyz') return Promise.resolve({ ok: false, status: 401 });
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDebugData) });
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<DebugPage />);

    const input = await screen.findByPlaceholderText('Admin token (fallback)');
    fireEvent.change(input, { target: { value: 'secret-xyz' } });
    fireEvent.click(screen.getByRole('button', { name: /unlock/i }));

    await waitFor(() => {
      expect(screen.getAllByText('scatter-basic').length).toBeGreaterThan(0);
    });
    expect(sessionStorage.getItem('anyplot.adminToken')).toBe('secret-xyz');
  });

  it('clears the stored token and re-prompts', async () => {
    sessionStorage.setItem('anyplot.adminToken', 'stored-token');
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 401 }))
    );

    render(<DebugPage />);

    const clearBtn = await screen.findByRole('button', { name: /clear stored token/i });
    fireEvent.click(clearBtn);

    await waitFor(() => {
      expect(sessionStorage.getItem('anyplot.adminToken')).toBeNull();
    });
    // Form is still on screen because fetch still returns 401.
    expect(screen.getByPlaceholderText('Admin token (fallback)')).toBeInTheDocument();
  });

  // The SPA-routed entry into /debug bypasses Cloudflare Access's page-level
  // intercept (no server roundtrip = no 302 to login). The first API fetch
  // then hits CF Access and 302s cross-origin to *.cloudflareaccess.com,
  // which fetch can't follow without CORS, surfacing as TypeError. The page
  // bootstraps the gate by triggering one top-level navigation.
  it('forces a top-level navigation on TypeError and sets the reload guard', async () => {
    sessionStorage.clear();
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    );
    const replaceSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, replace: replaceSpy, href: 'https://anyplot.ai/debug' },
    });

    render(<DebugPage />);

    await waitFor(() => {
      expect(replaceSpy).toHaveBeenCalledTimes(1);
    });
    expect(replaceSpy).toHaveBeenCalledWith('https://anyplot.ai/debug');
    expect(sessionStorage.getItem('anyplot.debugAuthReloaded')).toBe('1');
  });

  it('does not loop: second TypeError after the guard is set surfaces the error', async () => {
    sessionStorage.setItem('anyplot.debugAuthReloaded', '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    );
    const replaceSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, replace: replaceSpy, href: 'https://anyplot.ai/debug' },
    });

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
    expect(replaceSpy).not.toHaveBeenCalled();
  });

  // The debug feedback list ships a "copy Claude Code prompt" button next to
  // every message so admins can drop straight from triage into a Claude Code
  // session that already knows the URL, the reaction, and the user's text.
  it('copies a Claude-Code-ready prompt for a feedback message', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, origin: 'https://anyplot.ai', href: 'https://anyplot.ai/debug' },
    });

    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) => {
        if (url.includes('/debug/ping')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                database_connected: true,
                response_time_ms: 10,
                timestamp: '2026-05-21T00:00:00Z',
              }),
          });
        }
        if (url.includes('/debug/feedback/messages')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  id: 'fb-1',
                  message: 'Axis labels overlap on mobile',
                  reaction: 'bug',
                  contact: null,
                  path: '/plots/scatter-basic',
                  spec_id: 'scatter-basic',
                  viewport: '375x812',
                  status: 'new',
                  created_at: '2026-05-21T09:00:00Z',
                },
              ]),
          });
        }
        if (url.includes('/debug/feedback/top')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDebugData) });
      })
    );

    render(<DebugPage />);

    const copyBtn = await screen.findByRole('button', { name: /copy claude code prompt/i });
    fireEvent.click(copyBtn);

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    const copied = writeText.mock.calls[0][0] as string;
    expect(copied).toContain('https://anyplot.ai/plots/scatter-basic');
    expect(copied).toContain('bug report');
    expect(copied).toContain('> Axis labels overlap on mobile');
    expect(copied).toContain('Open a pull request');
  });
});

describe('DebugPage agent usage', () => {
  const USAGE = {
    status: 'ok',
    days: 7,
    sessions: 12,
    plots_shipped: 30,
    kept_rate: 0.42,
    kept_sessions: 5,
    shipped_sessions: 12,
    repair_rate: null,
    repaired_runs: 0,
    runs: 0,
    top_specs: [
      { key: 'scatter-basic', count: 5 },
      { key: 'bar-grouped', count: 2 },
    ],
    top_formats: [{ key: 'csv', count: 9 }],
    top_refusals: [],
    generated_at: '2026-10-16T12:00:00Z',
  };

  /** The page's own calls answered as in the tests above; the usage call by `usage`. */
  function stubFetch(usage: (days: string) => Promise<unknown>) {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/debug/agent-usage')) {
        return usage(new URL(url).searchParams.get('days') ?? '');
      }
      if (url.includes('/debug/agent/cases')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ items: [], has_more: false }),
        });
      }
      if (url.includes('/debug/feedback/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDebugData) });
    });
    vi.stubGlobal('fetch', fetchMock);
    return fetchMock;
  }

  const ok = (body: unknown) => Promise.resolve({ ok: true, json: () => Promise.resolve(body) });

  it('shows the tiles and the ranked lists of an ok answer', async () => {
    const fetchMock = stubFetch(() => ok(USAGE));
    render(<DebugPage />);

    const section = await screen.findByRole('region', { name: 'Agent usage section' });
    expect(await within(section).findByRole('group', { name: 'sessions' })).toHaveTextContent('12');
    expect(within(section).getByRole('group', { name: 'plots shipped' })).toHaveTextContent('30');
    // The counts behind the rate, so a percentage of a few sessions reads as what it is.
    expect(within(section).getByRole('group', { name: 'kept rate' })).toHaveTextContent(
      '42%5 of 12'
    );
    // No runs in the window: the rate has no base, and no counts.
    expect(within(section).getByRole('group', { name: 'repair rate' })).toHaveTextContent(
      /^—repair rate$/
    );
    const specs = within(section).getByRole('group', { name: 'top specs' });
    expect(
      within(specs)
        .getAllByRole('listitem')
        .map(item => item.textContent)
    ).toEqual(['5scatter-basic', '2bar-grouped']);
    expect(within(section).getByRole('group', { name: 'top formats' })).toHaveTextContent('9csv');
    expect(within(section).getByRole('group', { name: 'top refusal codes' })).toHaveTextContent(
      'none in this window'
    );
    const urls = fetchMock.mock.calls.map(call => call[0]);
    expect(urls.filter(url => url.includes('/debug/agent-usage'))).toEqual([
      expect.stringMatching(/\/debug\/agent-usage\?days=7$/),
    ]);
  });

  it('says that BigQuery is not configured yet, without tiles', async () => {
    stubFetch(() =>
      ok({ ...USAGE, status: 'not_configured', sessions: 0, plots_shipped: 0, kept_rate: null })
    );
    render(<DebugPage />);

    expect(await screen.findByTestId('agent-usage-empty')).toHaveTextContent(
      'BigQuery telemetry is not configured yet'
    );
    expect(screen.queryByRole('group', { name: 'kept rate' })).not.toBeInTheDocument();
  });

  it('says so for an empty window, a failed query and a failed request', async () => {
    let answer: () => Promise<unknown> = () =>
      ok({ ...USAGE, sessions: 0, plots_shipped: 0, top_specs: [], top_formats: [] });
    stubFetch(() => answer());
    render(<DebugPage />);
    expect(await screen.findByTestId('agent-usage-empty')).toHaveTextContent(
      'no sessions in this window'
    );

    answer = () => ok({ ...USAGE, status: 'unavailable' });
    fireEvent.click(screen.getByRole('button', { name: '30d' }));
    await waitFor(() =>
      expect(screen.getByTestId('agent-usage-empty')).toHaveTextContent(
        'usage data unavailable right now'
      )
    );

    answer = () => Promise.reject(new TypeError('Failed to fetch'));
    fireEvent.click(screen.getByRole('button', { name: '7d' }));
    await waitFor(() =>
      expect(screen.getByTestId('agent-usage-empty')).toHaveTextContent(
        'usage data unavailable right now'
      )
    );
    // The rest of the page stays.
    expect(screen.getAllByText('scatter-basic').length).toBeGreaterThan(0);
  });

  it('fetches the 30-day window on the toggle', async () => {
    const fetchMock = stubFetch(days =>
      ok({ ...USAGE, days: Number(days), sessions: days === '30' ? 77 : 12 })
    );
    render(<DebugPage />);

    expect(await screen.findByRole('group', { name: 'sessions' })).toHaveTextContent('12');
    expect(screen.getByRole('button', { name: '7d' })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('button', { name: '30d' }));
    await waitFor(() =>
      expect(screen.getByRole('group', { name: 'sessions' })).toHaveTextContent('77')
    );
    expect(screen.getByRole('button', { name: '30d' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('region', { name: 'Agent usage section' })).toHaveTextContent(
      'content-free telemetry · last 30 days'
    );
    const usageUrls = fetchMock.mock.calls
      .map(call => call[0])
      .filter(url => url.includes('/debug/agent-usage'));
    expect(usageUrls).toEqual([
      expect.stringMatching(/\?days=7$/),
      expect.stringMatching(/\?days=30$/),
    ]);
  });
});

describe('DebugPage spec matrix and feedback triage', () => {
  const TRIAGE_SPECS = [
    {
      id: 'bar-grouped',
      title: 'Zebra Bar Chart',
      updated: '2026-02-20T12:00:00',
      avg_score: 84.5,
      altair: 95,
      bokeh: 95,
      chartjs: 95,
      d3: 95,
      echarts: 95,
      ggplot2: 95,
      highcharts: 95,
      letsplot: 95,
      makie: 95,
      matplotlib: 95,
      muix: 95,
      plotly: 95,
      plotnine: 95,
      pygal: 95,
      seaborn: 78,
    },
    {
      id: 'heatmap-annotated',
      title: 'Alpha Heatmap',
      updated: '2026-03-10T12:00:00',
      avg_score: 91.0,
      altair: null,
      bokeh: null,
      chartjs: null,
      d3: null,
      echarts: null,
      ggplot2: null,
      highcharts: null,
      letsplot: null,
      makie: null,
      // One library below 90 while the average stays at 91.0: the low-score
      // filter must look at each library, not at the average.
      matplotlib: 85,
      muix: null,
      plotly: null,
      plotnine: null,
      pygal: null,
      seaborn: null,
    },
    {
      id: 'scatter-basic',
      title: 'Middle Scatter',
      updated: '2026-01-15T12:00:00',
      avg_score: 96.0,
      altair: 96,
      bokeh: 96,
      chartjs: 96,
      d3: 96,
      echarts: 96,
      ggplot2: 96,
      highcharts: 96,
      letsplot: 96,
      makie: 96,
      matplotlib: 96,
      muix: 96,
      plotly: 96,
      plotnine: 96,
      pygal: 96,
      seaborn: 96,
    },
  ];

  const TRIAGE_MESSAGES = [
    {
      id: 'fb-1',
      message: 'Axis labels overlap on mobile',
      reaction: 'bug',
      contact: 'alice@example.com',
      path: '/scatter-basic',
      spec_id: 'scatter-basic',
      viewport: '375x812',
      status: 'new' as const,
      created_at: '2026-05-21T09:00:00',
    },
  ];

  beforeEach(({ onTestFinished }) => {
    vi.clearAllMocks();
    sessionStorage.clear();
    onTestFinished(() => {
      sessionStorage.clear();
      vi.useRealTimers();
      vi.unstubAllGlobals();
    });
  });

  function renderedSpecOrder(): string[] {
    const knownIds = new Set(TRIAGE_SPECS.map(s => s.id));
    return screen
      .getAllByRole('link')
      .map(link => link.textContent ?? '')
      .filter(text => knownIds.has(text));
  }

  function expectSortState(
    activeCol: 'spec id' | 'title' | 'avg' | 'updated',
    dir: 'asc' | 'desc',
    expectedOrder: string[]
  ) {
    expect(renderedSpecOrder()).toEqual(expectedOrder);
    const arrow = dir === 'asc' ? '▲' : '▼';
    for (const label of ['spec id', 'title', 'avg', 'updated'] as const) {
      const btn = screen.getByRole('button', { name: new RegExp(`^${label}`) });
      if (label === activeCol) {
        expect(btn).toHaveTextContent(arrow);
      } else {
        expect(btn).not.toHaveTextContent(/[▲▼]/);
      }
    }
  }

  function stubPageFetch(options?: { patchStatus?: () => number }) {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes('/debug/ping')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              database_connected: true,
              response_time_ms: 10,
              timestamp: '2026-05-21T12:00:00',
            }),
        });
      }
      if (url.includes('/debug/agent-usage')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              status: 'not_configured',
              days: 7,
              sessions: 0,
              plots_shipped: 0,
              kept_rate: null,
              kept_sessions: 0,
              shipped_sessions: 0,
              repair_rate: null,
              repaired_runs: 0,
              runs: 0,
              top_specs: [],
              top_formats: [],
              top_refusals: [],
              generated_at: '2026-05-21T12:00:00',
            }),
        });
      }
      if (url.includes('/debug/agent/cases')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ items: [], has_more: false }),
        });
      }
      if (url.includes('/debug/feedback/messages')) {
        const parsed = new URL(url, 'https://api.anyplot.ai');
        const status = parsed.searchParams.get('status');
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(status === 'open' ? TRIAGE_MESSAGES : []),
        });
      }
      if (url.includes('/debug/feedback/top')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (init?.method === 'PATCH') {
        const status = options?.patchStatus?.() ?? 200;
        return Promise.resolve({
          ok: status >= 200 && status < 300,
          status,
          json: () => Promise.resolve({ status: 'ok' }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockDebugData,
            total_specs: TRIAGE_SPECS.length,
            specs: TRIAGE_SPECS,
          }),
      });
    });
    vi.stubGlobal('fetch', fetchMock);
    return fetchMock;
  }

  it('sorts specs by each sortable header with per-column default direction and toggles on second click', async () => {
    stubPageFetch();
    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText('3 / 3')).toBeInTheDocument();
    });

    // Initial sort is updated descending
    expectSortState('updated', 'desc', ['heatmap-annotated', 'bar-grouped', 'scatter-basic']);

    // Second click on updated toggles to ascending
    fireEvent.click(screen.getByRole('button', { name: /^updated/ }));
    expectSortState('updated', 'asc', ['scatter-basic', 'bar-grouped', 'heatmap-annotated']);

    // Clicking spec id defaults to ascending, second click toggles to descending
    fireEvent.click(screen.getByRole('button', { name: /^spec id/ }));
    expectSortState('spec id', 'asc', ['bar-grouped', 'heatmap-annotated', 'scatter-basic']);

    fireEvent.click(screen.getByRole('button', { name: /^spec id/ }));
    expectSortState('spec id', 'desc', ['scatter-basic', 'heatmap-annotated', 'bar-grouped']);

    // Clicking title defaults to ascending, second click toggles to descending
    fireEvent.click(screen.getByRole('button', { name: /^title/ }));
    expectSortState('title', 'asc', ['heatmap-annotated', 'scatter-basic', 'bar-grouped']);

    fireEvent.click(screen.getByRole('button', { name: /^title/ }));
    expectSortState('title', 'desc', ['bar-grouped', 'scatter-basic', 'heatmap-annotated']);

    // Clicking avg defaults to descending, second click toggles to ascending
    fireEvent.click(screen.getByRole('button', { name: /^avg/ }));
    expectSortState('avg', 'desc', ['scatter-basic', 'heatmap-annotated', 'bar-grouped']);

    fireEvent.click(screen.getByRole('button', { name: /^avg/ }));
    expectSortState('avg', 'asc', ['bar-grouped', 'heatmap-annotated', 'scatter-basic']);

    // Clicking updated from another column defaults to descending
    fireEvent.click(screen.getByRole('button', { name: /^updated/ }));
    expectSortState('updated', 'desc', ['heatmap-annotated', 'bar-grouped', 'scatter-basic']);
  });

  it('narrows rows with incomplete and low-score filters and restores them on second click', async () => {
    stubPageFetch();
    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByText('3 / 3')).toBeInTheDocument();
    });

    const incompleteBtn = screen.getByRole('button', { name: /incomplete <15/i });
    fireEvent.click(incompleteBtn);
    expect(screen.getByText('1 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated']);

    fireEvent.click(incompleteBtn);
    expect(screen.getByText('3 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated', 'bar-grouped', 'scatter-basic']);

    const lowScoresBtn = screen.getByRole('button', { name: /low scores <90/i });
    fireEvent.click(lowScoresBtn);
    expect(screen.getByText('2 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated', 'bar-grouped']);

    fireEvent.click(lowScoresBtn);
    expect(screen.getByText('3 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated', 'bar-grouped', 'scatter-basic']);
  });

  it('patches feedback status with X-Admin-Token, reverts on 500, and refetches when status filter changes', async () => {
    sessionStorage.setItem('anyplot.adminToken', 'admin-secret');
    let nextPatchStatus = 200;
    const fetchMock = stubPageFetch({ patchStatus: () => nextPatchStatus });

    render(<DebugPage />);

    const msgText = await screen.findByText('Axis labels overlap on mobile');
    const msgRow = msgText.parentElement?.parentElement;
    expect(msgRow).not.toBeNull();
    const statusSelect = within(msgRow as HTMLElement).getByRole('combobox');
    expect(statusSelect).toHaveValue('new');

    fireEvent.change(statusSelect, { target: { value: 'done' } });
    expect(statusSelect).toHaveValue('done');

    await waitFor(() => {
      const patchCalls = fetchMock.mock.calls.filter(call => call[1]?.method === 'PATCH');
      expect(patchCalls).toHaveLength(1);
    });
    const [patchUrl, patchInit] = fetchMock.mock.calls.find(call => call[1]?.method === 'PATCH')!;
    expect(patchUrl).toMatch(/\/debug\/feedback\/fb-1$/);
    expect(patchInit?.body).toBe(JSON.stringify({ status: 'done' }));
    expect((patchInit?.headers as Record<string, string>)?.['X-Admin-Token']).toBe('admin-secret');

    // When PATCH answers 500, the select reverts to the previous status
    nextPatchStatus = 500;
    fireEvent.change(statusSelect, { target: { value: 'wont_solve' } });
    await waitFor(() => {
      expect(statusSelect).toHaveValue('done');
    });

    // Choosing a status filter refetches .../debug/feedback/messages?status=<status>&limit=50
    const messagesHeaderBar = screen.getByRole('heading', { name: 'feedback · messages' })
      .parentElement?.parentElement;
    expect(messagesHeaderBar).not.toBeNull();
    const filterSelect = within(messagesHeaderBar as HTMLElement).getByRole('combobox');
    fireEvent.change(filterSelect, { target: { value: 'done' } });

    await waitFor(() => {
      const messageUrls = fetchMock.mock.calls
        .map(call => call[0])
        .filter(url => url.includes('/debug/feedback/messages'));
      expect(messageUrls).toContainEqual(
        expect.stringMatching(/\/debug\/feedback\/messages\?status=done&limit=50$/)
      );
    });
  });
});
