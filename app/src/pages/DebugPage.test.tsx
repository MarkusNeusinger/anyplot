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
    repair_rate: null,
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
    expect(within(section).getByRole('group', { name: 'kept rate' })).toHaveTextContent('42%');
    // No runs in the window: the rate has no base.
    expect(within(section).getByRole('group', { name: 'repair rate' })).toHaveTextContent('—');
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
