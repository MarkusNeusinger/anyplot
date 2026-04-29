import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen, waitFor } from '../test-utils';

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
    expect(screen.getByText(/loading debug data/i)).toBeInTheDocument();
  });

  it('renders debug data after fetch', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/debug/ping')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ database_connected: true, response_time_ms: 42, timestamp: '2026-04-24T12:00:00Z' }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockDebugData) });
    }));

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getAllByText('scatter-basic').length).toBeGreaterThan(0);
    });
  });

  it('handles fetch error gracefully', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/debug/ping')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ database_connected: false, response_time_ms: 0, timestamp: '' }) });
      }
      return Promise.resolve({ ok: false, status: 500 });
    }));

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
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 401 })));

    render(<DebugPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Admin token (fallback)')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /unlock/i })).toBeInTheDocument();
    expect(screen.getByText(/admin token required/i)).toBeInTheDocument();
  });

  it('renders the admin-token form on 503 with the not-configured hint', async () => {
    sessionStorage.clear();
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 503 })));

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
          json: () => Promise.resolve({ status: 403, message: 'User stranger@example.com not authorized', path: '/debug/status' }),
        }),
      ),
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
          json: () => Promise.resolve({ database_connected: true, response_time_ms: 10, timestamp: '2026-04-27T00:00:00Z' }),
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
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 401 })));

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
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))));
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
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))));
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

});
