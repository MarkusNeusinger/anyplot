import { useState, useEffect, useMemo } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';

import { DEBUG_API_URL, LIBRARIES, LIB_ABBREV } from '../constants';
import { specPath } from '../utils/paths';
import { SectionHeader } from '../components/SectionHeader';
import { typography, colors, semanticColors, fontSize } from '../theme';

// ============================================================================
// Types
// ============================================================================

interface SpecStatus {
  id: string;
  title: string;
  updated: string | null;
  avg_score: number | null;
  altair: number | null;
  bokeh: number | null;
  highcharts: number | null;
  letsplot: number | null;
  matplotlib: number | null;
  plotly: number | null;
  plotnine: number | null;
  pygal: number | null;
  seaborn: number | null;
}

interface LibraryStats {
  id: string;
  name: string;
  impl_count: number;
  avg_score: number | null;
  min_score: number | null;
  max_score: number | null;
}

interface ProblemSpec {
  id: string;
  title: string;
  issue: string;
  value: string | null;
}

interface SystemHealth {
  database_connected: boolean;
  api_response_time_ms: number;
  timestamp: string;
  total_specs_in_db: number;
  total_impls_in_db: number;
}

interface DailyImplPoint {
  date: string;
  impls_updated: number;
}

interface RecentActivity {
  spec_id: string;
  spec_title: string;
  library_id: string;
  quality_score: number | null;
  generated_by: string | null;
  updated: string;
}

interface WeaknessCount {
  text: string;
  count: number;
}

interface DebugStatus {
  total_specs: number;
  total_implementations: number;
  coverage_percent: number;
  library_stats: LibraryStats[];
  low_score_specs: ProblemSpec[];
  oldest_specs: ProblemSpec[];
  missing_preview_specs: ProblemSpec[];
  missing_tags_specs: ProblemSpec[];
  daily_impls: DailyImplPoint[];
  recent_activity: RecentActivity[];
  common_weaknesses: WeaknessCount[];
  system: SystemHealth;
  specs: SpecStatus[];
}

type SortKey = 'updated' | 'id' | 'title' | 'avg_score';
type SortDir = 'asc' | 'desc';

// ============================================================================
// Helpers
// ============================================================================

const LOW_SCORE_THRESHOLD = 90;

function scoreColor(score: number | null): string {
  if (score === null) return 'var(--ink-muted)';
  if (score >= 90) return colors.success;
  if (score >= 75) return colors.warning;
  return colors.error;
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diffSec = Math.max(0, (Date.now() - then) / 1000);
  if (diffSec < 60) return `${Math.floor(diffSec)}s ago`;
  const diffMin = diffSec / 60;
  if (diffMin < 60) return `${Math.floor(diffMin)}m ago`;
  const diffHr = diffMin / 60;
  if (diffHr < 24) return `${Math.floor(diffHr)}h ago`;
  const diffDay = diffHr / 24;
  if (diffDay < 30) return `${Math.floor(diffDay)}d ago`;
  const diffMon = diffDay / 30;
  if (diffMon < 12) return `${Math.floor(diffMon)}mo ago`;
  return `${Math.floor(diffMon / 12)}y ago`;
}

function formatDateShort(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Styled native input / select / button using CSS vars
const nativeControlSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xs,
  color: 'var(--ink)',
  bgcolor: 'var(--bg-surface)',
  border: '1px solid var(--rule)',
  borderRadius: '4px',
  px: 1,
  py: 0.75,
  outline: 'none',
  '&:focus': { borderColor: colors.primary },
} as const;

// ============================================================================
// Component
// ============================================================================

const PING_INTERVAL_MS = 2000;
const PING_HISTORY = 30;

function pingColor(ms: number): string {
  if (ms < 75) return colors.success;
  if (ms < 200) return colors.warning;
  return colors.error;
}

// Admin auth for /debug endpoints (require_admin in api/routers/debug.py).
// Two paths:
//   - Cloudflare Access cookie set on .anyplot.ai → forwarded as Cf-Access-Jwt-Assertion
//     to api.anyplot.ai. credentials: 'include' is required for the cookie to
//     travel cross-origin to the API.
//   - X-Admin-Token header as a fallback (CI, break-glass, local dev). Stored
//     in sessionStorage so it survives reloads of the same tab without
//     persisting across browser sessions.
const ADMIN_TOKEN_KEY = 'anyplot.adminToken';
const readAdminToken = (): string => {
  try { return sessionStorage.getItem(ADMIN_TOKEN_KEY) ?? ''; } catch { return ''; }
};
const writeAdminToken = (value: string): void => {
  try { sessionStorage.setItem(ADMIN_TOKEN_KEY, value); } catch { /* sessionStorage may be unavailable */ }
};
const clearAdminToken = (): void => {
  try { sessionStorage.removeItem(ADMIN_TOKEN_KEY); } catch { /* noop */ }
};

const adminFetch = (url: string, token: string): Promise<Response> =>
  fetch(url, {
    credentials: 'include',
    headers: token ? { 'X-Admin-Token': token } : undefined,
  });

export function DebugPage() {
  const [data, setData] = useState<DebugStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authRequired, setAuthRequired] = useState(false);
  const [adminToken, setAdminToken] = useState<string>(() => readAdminToken());
  const [tokenInput, setTokenInput] = useState('');
  const [reloadCounter, setReloadCounter] = useState(0);
  const [sortKey, setSortKey] = useState<SortKey>('updated');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const [searchText, setSearchText] = useState('');
  const [showIncomplete, setShowIncomplete] = useState(false);
  const [showLowScores, setShowLowScores] = useState(false);
  const [missingLibrary, setMissingLibrary] = useState('');

  const [pings, setPings] = useState<Array<{ ms: number; ok: boolean }>>([]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    adminFetch(`${DEBUG_API_URL}/debug/status`, adminToken)
      .then(async r => {
        // Reaching the .then path means the fetch resolved cleanly — clear
        // the one-shot reload guard so a future cross-origin redirect can
        // re-trigger the bootstrap.
        try { sessionStorage.removeItem('anyplot.debugAuthReloaded'); } catch {}
        // 403 is the Cloudflare Access JWT path's denial: a signed-in Google
        // account that isn't on the admin_allowed_emails allow-list. Surface
        // it on the auth-required screen with the server's message so the
        // user knows to sign in with a different account or ask for access.
        if (r.status === 401 || r.status === 403 || r.status === 503) {
          setAuthRequired(true);
          if (r.status === 403) {
            const body = await r.json().catch(() => ({}));
            throw new Error(body?.message || 'this account is not authorized for /debug');
          }
          throw new Error(r.status === 503 ? 'admin auth not configured on server' : 'admin token required');
        }
        if (!r.ok) throw new Error(`${r.status}`);
        setAuthRequired(false);
        return r.json();
      })
      .then(setData)
      .catch(e => {
        // SPA-routed entry to /debug bypasses the Cloudflare Access page-
        // level intercept. The first API fetch then 302s cross-origin to
        // *.cloudflareaccess.com, which fetch can't follow without CORS,
        // surfacing as TypeError("Failed to fetch"). Force one top-level
        // navigation so CF Access can intercept the page request and bounce
        // to Google login. sessionStorage guard keeps this from looping if
        // the second load ALSO fails (e.g. wrong allow-list).
        if (e instanceof TypeError) {
          let alreadyTried = false;
          try { alreadyTried = !!sessionStorage.getItem('anyplot.debugAuthReloaded'); } catch {}
          if (!alreadyTried) {
            try { sessionStorage.setItem('anyplot.debugAuthReloaded', '1'); } catch {}
            window.location.assign(window.location.href);
            return;
          }
        }
        setError(e.message || 'failed to load');
      })
      .finally(() => setLoading(false));
  }, [adminToken, reloadCounter]);

  useEffect(() => {
    if (authRequired) return;
    let cancelled = false;
    const tick = async () => {
      const started = performance.now();
      try {
        const r = await adminFetch(`${DEBUG_API_URL}/debug/ping`, adminToken);
        const totalMs = performance.now() - started;
        if (!r.ok) throw new Error(`${r.status}`);
        const json: { database_connected: boolean } = await r.json();
        if (cancelled) return;
        setPings(prev => [...prev.slice(-(PING_HISTORY - 1)), { ms: totalMs, ok: json.database_connected }]);
      } catch {
        if (cancelled) return;
        const totalMs = performance.now() - started;
        setPings(prev => [...prev.slice(-(PING_HISTORY - 1)), { ms: totalMs, ok: false }]);
      }
    };
    tick();
    const id = setInterval(tick, PING_INTERVAL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, [adminToken, authRequired]);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = tokenInput.trim();
    if (!trimmed) return;
    writeAdminToken(trimmed);
    setAdminToken(trimmed);
    setTokenInput('');
  };

  const handleTokenClear = () => {
    clearAdminToken();
    setAdminToken('');
    setReloadCounter(c => c + 1);
  };

  const countImpls = (spec: SpecStatus): number =>
    LIBRARIES.filter(lib => spec[lib as keyof SpecStatus] !== null).length;

  const hasLowScore = (spec: SpecStatus): boolean =>
    LIBRARIES.some(lib => {
      const s = spec[lib as keyof SpecStatus] as number | null;
      return s !== null && s < LOW_SCORE_THRESHOLD;
    });

  const filteredSpecs = useMemo(() => {
    if (!data) return [];
    let filtered = [...data.specs];

    if (searchText) {
      const q = searchText.toLowerCase();
      filtered = filtered.filter(s => s.id.toLowerCase().includes(q) || s.title.toLowerCase().includes(q));
    }
    if (showIncomplete) filtered = filtered.filter(s => countImpls(s) < 9);
    if (showLowScores) filtered = filtered.filter(hasLowScore);
    if (missingLibrary) filtered = filtered.filter(s => s[missingLibrary as keyof SpecStatus] === null);

    filtered.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'updated': cmp = (a.updated || '').localeCompare(b.updated || ''); break;
        case 'id': cmp = a.id.localeCompare(b.id); break;
        case 'title': cmp = a.title.localeCompare(b.title); break;
        case 'avg_score': cmp = (a.avg_score ?? 0) - (b.avg_score ?? 0); break;
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });

    return filtered;
  }, [data, searchText, showIncomplete, showLowScores, missingLibrary, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'updated' || key === 'avg_score' ? 'desc' : 'asc');
    }
  };

  if (authRequired) {
    return (
      <Box sx={{ py: 4, maxWidth: 420, mx: 'auto' }}>
        <SectionHeader prompt="❯" title={<em>debug · admin auth</em>} />
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mb: 2 }}>
          {error || 'sign in via your browser session, or paste an admin token as a fallback.'}
        </Typography>
        <Box component="form" onSubmit={handleTokenSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box
            component="input"
            type="password"
            autoFocus
            placeholder="Admin token (fallback)"
            value={tokenInput}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTokenInput(e.target.value)}
            sx={nativeControlSx}
          />
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Box
              component="button"
              type="submit"
              sx={{
                ...nativeControlSx,
                cursor: 'pointer',
                bgcolor: colors.primary,
                color: 'var(--bg-page)',
                borderColor: colors.primary,
                fontWeight: 600,
              }}
            >
              unlock
            </Box>
            {adminToken && (
              <Box
                component="button"
                type="button"
                onClick={handleTokenClear}
                sx={{ ...nativeControlSx, cursor: 'pointer' }}
              >
                clear stored token
              </Box>
            )}
          </Box>
          <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText, mt: 1 }}>
            stored in sessionStorage — clears when this tab closes.
          </Typography>
        </Box>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText }}>
          loading debug data...
        </Typography>
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography sx={{ fontFamily: typography.fontFamily, color: colors.error }}>
          failed to load{error ? `: ${error}` : ''}
        </Typography>
      </Box>
    );
  }

  // Derived KPIs
  const totalImplsWithScore = data.library_stats.reduce(
    (acc, l) => acc + (l.avg_score !== null ? l.impl_count : 0), 0
  );
  const weightedScoreSum = data.library_stats.reduce(
    (acc, l) => acc + (l.avg_score !== null ? l.avg_score * l.impl_count : 0), 0
  );
  const avgQuality = totalImplsWithScore > 0 ? weightedScoreSum / totalImplsWithScore : null;

  const maxDaily = Math.max(...data.daily_impls.map(p => p.impls_updated), 1);
  const maxLibCount = Math.max(...data.library_stats.map(l => l.impl_count), 1);
  const maxWeakness = Math.max(...data.common_weaknesses.map(w => w.count), 1);

  const kpis: Array<{ label: string; value: number | null; suffix?: string }> = [
    { label: 'specs', value: data.total_specs },
    { label: 'impls', value: data.total_implementations },
    { label: 'coverage', value: data.coverage_percent, suffix: '%' },
    { label: 'avg quality', value: avgQuality !== null ? Math.round(avgQuality * 10) / 10 : null },
    { label: 'low score', value: data.low_score_specs.length },
    { label: 'stale specs', value: data.oldest_specs.length },
  ];

  const firstDate = data.daily_impls[0]?.date ?? '';
  const lastDate = data.daily_impls[data.daily_impls.length - 1]?.date ?? '';

  return (
    <Box sx={{ pt: { xs: 2, md: 3 }, pb: 4 }}>
      {/* Header */}
      <SectionHeader prompt="❯" title={<em>debug</em>} />

      {/* System health row */}
      {(() => {
        const latest = pings[pings.length - 1];
        const okPings = pings.filter(p => p.ok);
        const currentOk = latest ? latest.ok : data.system.database_connected;
        const currentMs = latest ? latest.ms : data.system.api_response_time_ms;
        const avgMs = okPings.length > 0 ? okPings.reduce((a, p) => a + p.ms, 0) / okPings.length : null;
        const maxMs = Math.max(...pings.map(p => p.ms), 1);
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: { xs: 1.5, md: 3 }, mt: -2, mb: 3, fontSize: fontSize.xs, fontFamily: typography.fontFamily }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: currentOk ? colors.success : colors.error }} />
              <Typography component="span" sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: 'var(--ink-soft)' }}>
                database {currentOk ? 'connected' : 'down'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip
                title={avgMs !== null ? `avg ${avgMs.toFixed(0)}ms · max ${maxMs.toFixed(0)}ms · ${pings.length} samples` : 'measuring...'}
                arrow
              >
                <Box sx={{
                  display: 'flex', alignItems: 'flex-end', gap: '1px',
                  height: 18, width: PING_HISTORY * 4,
                  borderBottom: '1px solid var(--rule)', px: 0.25,
                }}>
                  {Array.from({ length: PING_HISTORY }).map((_, i) => {
                    const idx = pings.length - PING_HISTORY + i;
                    const p = idx >= 0 ? pings[idx] : null;
                    if (!p) return <Box key={i} sx={{ flex: 1 }} />;
                    return (
                      <Box
                        key={i}
                        sx={{
                          flex: 1,
                          height: p.ok ? `${Math.max((p.ms / maxMs) * 100, 8)}%` : '100%',
                          bgcolor: p.ok ? pingColor(p.ms) : colors.error,
                          opacity: 0.7,
                        }}
                      />
                    );
                  })}
                </Box>
              </Tooltip>
              <Typography component="span" sx={{
                fontFamily: typography.fontFamily, fontSize: fontSize.xs,
                color: currentOk ? pingColor(currentMs) : colors.error,
                fontWeight: 600, minWidth: 52,
              }}>
                {currentMs.toFixed(0)}ms
              </Typography>
              {avgMs !== null && (
                <Typography component="span" sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText }}>
                  avg {avgMs.toFixed(0)}
                </Typography>
              )}
            </Box>
            <Typography component="span" sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText }}>
              updated {new Date(data.system.timestamp).toLocaleTimeString()}
            </Typography>
          </Box>
        );
      })()}

      {/* KPI Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(6, 1fr)' }, gap: 2, mb: 4 }}>
        {kpis.map(item => (
          <Box key={item.label} sx={{ textAlign: 'center', p: 2, border: '1px solid var(--rule)', borderRadius: 1 }}>
            <Typography sx={{ fontFamily: typography.serif, fontSize: '2rem', fontWeight: 300, color: 'var(--ink)', lineHeight: 1.2 }}>
              {typeof item.value === 'number' ? `${formatNum(item.value)}${item.suffix ?? ''}` : '—'}
            </Typography>
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mt: 0.5 }}>
              {item.label}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Daily Activity Bar Chart */}
      <SectionHeader prompt="❯" title={<em>daily activity</em>} />
      <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mb: 1 }}>
        implementation updates · last 30 days
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.25, height: 70, overflow: 'hidden' }}>
        {data.daily_impls.map(point => (
          <Tooltip key={point.date} title={`${point.date}: ${point.impls_updated} impls`} arrow>
            <Box sx={{
              flex: 1,
              height: `${Math.max((point.impls_updated / maxDaily) * 100, point.impls_updated > 0 ? 3 : 0)}%`,
              bgcolor: colors.primaryDark,
              opacity: 0.5,
              borderRadius: '2px 2px 0 0',
              minHeight: point.impls_updated > 0 ? 2 : 0,
              '&:hover': { opacity: 0.8 },
              transition: 'opacity 0.15s ease',
            }} />
          </Tooltip>
        ))}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText }}>
          {firstDate}
        </Typography>
        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.micro, color: semanticColors.mutedText }}>
          {lastDate}
        </Typography>
      </Box>

      {/* Library Coverage */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>libraries</em>} />
      </Box>
      <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, mb: 1 }}>
        impl count · avg · min–max
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {[...data.library_stats].sort((a, b) => b.impl_count - a.impl_count).map(lib => (
          <Box
            key={lib.id}
            sx={{
              display: 'grid',
              gridTemplateColumns: '80px 1fr 40px 40px 70px',
              gap: 1.5,
              alignItems: 'center',
              fontFamily: typography.fontFamily,
              fontSize: fontSize.xxs,
            }}
          >
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText, textAlign: 'right' }}>
              {lib.name}
            </Typography>
            <Box sx={{ height: 10, bgcolor: 'var(--bg-elevated)', borderRadius: '2px', overflow: 'hidden' }}>
              <Box sx={{
                width: `${(lib.impl_count / maxLibCount) * 100}%`,
                height: '100%',
                bgcolor: colors.primaryDark,
                opacity: 0.5,
              }} />
            </Box>
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: 'var(--ink-soft)', fontWeight: 600, textAlign: 'right' }}>
              {lib.impl_count}
            </Typography>
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: scoreColor(lib.avg_score), fontWeight: 600, textAlign: 'right' }}>
              {lib.avg_score ?? '—'}
            </Typography>
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText, textAlign: 'right' }}>
              {lib.min_score?.toFixed(0) ?? '—'}–{lib.max_score?.toFixed(0) ?? '—'}
            </Typography>
          </Box>
        ))}
      </Box>
      <Box sx={{
        display: 'grid',
        gridTemplateColumns: '80px 1fr 40px 40px 70px',
        gap: 1.5,
        mt: 0.5,
        fontFamily: typography.fontFamily,
        fontSize: fontSize.micro,
        color: semanticColors.mutedText,
      }}>
        <span />
        <span />
        <Box component="span" sx={{ textAlign: 'right' }}>count</Box>
        <Box component="span" sx={{ textAlign: 'right' }}>avg</Box>
        <Box component="span" sx={{ textAlign: 'right' }}>min–max</Box>
      </Box>

      {/* Recent Activity */}
      {data.recent_activity.length > 0 && (
        <>
          <Box sx={{ mt: 4 }}>
            <SectionHeader prompt="❯" title={<em>recent activity</em>} />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {data.recent_activity.map((act, idx) => (
              <Link
                key={`${act.spec_id}-${act.library_id}-${idx}`}
                component={RouterLink}
                to={specPath(act.spec_id, 'python', act.library_id)}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '55px 1fr 30px', sm: '65px 90px minmax(0, 1fr) 30px 130px' },
                  gap: { xs: 1, sm: 1.5 },
                  alignItems: 'center',
                  textDecoration: 'none',
                  color: 'inherit',
                  py: 0.5,
                  borderBottom: '1px solid var(--rule)',
                  '&:hover': { bgcolor: 'var(--bg-surface)' },
                }}
              >
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: semanticColors.mutedText }}>
                  {timeAgo(act.updated)}
                </Typography>
                <Typography sx={{
                  fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: 'var(--ink-soft)',
                  display: { xs: 'none', sm: 'block' },
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {act.library_id}
                </Typography>
                <Typography sx={{
                  fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: 'var(--ink)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0,
                }}>
                  <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' }, color: semanticColors.mutedText, mr: 0.5 }}>
                    {act.library_id} ·
                  </Box>
                  {act.spec_title}
                </Typography>
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: scoreColor(act.quality_score), fontWeight: 600, textAlign: 'right' }}>
                  {act.quality_score !== null ? Math.round(act.quality_score) : '—'}
                </Typography>
                <Typography sx={{
                  fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText,
                  display: { xs: 'none', sm: 'block' },
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  textAlign: 'right',
                }}>
                  {act.generated_by ?? '—'}
                </Typography>
              </Link>
            ))}
          </Box>
        </>
      )}

      {/* Common Weaknesses */}
      {data.common_weaknesses.length > 0 && (
        <>
          <Box sx={{ mt: 4 }}>
            <SectionHeader prompt="❯" title={<em>common weaknesses</em>} />
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, alignItems: 'baseline' }}>
            {data.common_weaknesses.map(w => {
              const ratio = w.count / maxWeakness;
              const size = ratio >= 0.8 ? fontSize.md : ratio >= 0.5 ? fontSize.sm : ratio >= 0.25 ? fontSize.xs : fontSize.xxs;
              const weight = ratio >= 0.5 ? 600 : 400;
              const opacity = ratio >= 0.8 ? 1 : ratio >= 0.5 ? 0.85 : ratio >= 0.25 ? 0.7 : 0.55;
              return (
                <Box key={w.text} sx={{
                  fontFamily: typography.fontFamily, fontSize: size, fontWeight: weight,
                  color: 'var(--ink-soft)', opacity, px: 0.75, py: 0.25, borderRadius: 0.5,
                  bgcolor: 'var(--bg-surface)', border: '1px solid var(--rule)',
                }}>
                  {w.text}
                  <Box component="span" sx={{ fontSize: fontSize.micro, color: semanticColors.mutedText, ml: 0.5 }}>
                    {w.count}
                  </Box>
                </Box>
              );
            })}
          </Box>
        </>
      )}

      {/* Problem Areas */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>problem areas</em>} />
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {[
          { title: `low scores (avg < ${LOW_SCORE_THRESHOLD})`, items: data.low_score_specs },
          { title: 'missing previews', items: data.missing_preview_specs },
          { title: 'missing tags', items: data.missing_tags_specs },
          { title: 'oldest specs', items: data.oldest_specs },
        ].map(section => (
          <Box
            key={section.title}
            component="details"
            sx={{
              border: '1px solid var(--rule)', borderRadius: 1, p: 0,
              '& > summary': { cursor: 'pointer', listStyle: 'none' },
              '& > summary::-webkit-details-marker': { display: 'none' },
            }}
          >
            <Box
              component="summary"
              sx={{
                display: 'flex', alignItems: 'center', gap: 1, px: 1.5, py: 1,
                fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: 'var(--ink-soft)',
              }}
            >
              <Box component="span" sx={{ color: semanticColors.mutedText }}>▸</Box>
              <Box component="span" sx={{ fontWeight: 600 }}>{section.title}</Box>
              <Box component="span" sx={{ color: semanticColors.mutedText }}>
                {section.items.length}
              </Box>
            </Box>
            {section.items.length > 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--rule)' }}>
                {section.items.map((item, idx) => (
                  <Link
                    key={`${item.id}-${idx}`}
                    component={RouterLink}
                    to={specPath(item.id)}
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr auto', sm: 'minmax(140px, 200px) 1fr auto' },
                      gap: 1, px: 1.5, py: 0.75, alignItems: 'center',
                      textDecoration: 'none', color: 'inherit',
                      fontFamily: typography.fontFamily, fontSize: fontSize.xs,
                      borderTop: idx > 0 ? '1px solid var(--rule)' : 'none',
                      '&:hover': { bgcolor: 'var(--bg-surface)' },
                    }}
                  >
                    <Box component="span" sx={{ color: colors.primary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.id}
                    </Box>
                    <Box component="span" sx={{ color: semanticColors.mutedText, display: { xs: 'none', sm: 'inline' }, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.issue}
                    </Box>
                    {item.value && (
                      <Box component="span" sx={{ color: colors.error, whiteSpace: 'nowrap', textAlign: 'right' }}>
                        {item.value}
                      </Box>
                    )}
                  </Link>
                ))}
              </Box>
            )}
          </Box>
        ))}
      </Box>

      {/* Spec Matrix */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>specs</em>} />
      </Box>

      {/* Filter Bar */}
      <Box sx={{
        display: 'flex', gap: 1, mb: 2, flexWrap: { xs: 'nowrap', sm: 'wrap' },
        overflowX: { xs: 'auto', sm: 'visible' }, pb: { xs: 0.5, sm: 0 },
      }}>
        <Box
          component="input"
          type="search"
          placeholder="search spec id or title..."
          value={searchText}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchText(e.target.value)}
          sx={{ ...nativeControlSx, flex: { xs: '0 0 180px', sm: '1 1 220px' } }}
        />
        <Box
          component="button"
          type="button"
          onClick={() => setShowIncomplete(v => !v)}
          sx={{
            ...nativeControlSx,
            cursor: 'pointer',
            flexShrink: 0,
            bgcolor: showIncomplete ? colors.highlight.bg : 'var(--bg-surface)',
            color: showIncomplete ? colors.highlight.text : 'var(--ink-soft)',
            borderColor: showIncomplete ? colors.primary : 'var(--rule)',
          }}
        >
          incomplete {'<'}9
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => setShowLowScores(v => !v)}
          sx={{
            ...nativeControlSx,
            cursor: 'pointer',
            flexShrink: 0,
            bgcolor: showLowScores ? colors.highlight.bg : 'var(--bg-surface)',
            color: showLowScores ? colors.highlight.text : 'var(--ink-soft)',
            borderColor: showLowScores ? colors.primary : 'var(--rule)',
          }}
        >
          low scores {'<'}90
        </Box>
        <Box
          component="select"
          value={missingLibrary}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMissingLibrary(e.target.value)}
          sx={{ ...nativeControlSx, cursor: 'pointer', flexShrink: 0 }}
        >
          <option value="">missing library: any</option>
          {LIBRARIES.map(lib => (
            <option key={lib} value={lib}>missing: {lib}</option>
          ))}
        </Box>
        <Typography sx={{
          fontFamily: typography.fontFamily, fontSize: fontSize.xs,
          color: semanticColors.mutedText, alignSelf: 'center', flexShrink: 0, ml: { xs: 0, sm: 'auto' },
        }}>
          {filteredSpecs.length} / {data.total_specs}
        </Typography>
      </Box>

      {/* Desktop: grid matrix */}
      <Box sx={{ display: { xs: 'none', md: 'block' }, overflowX: 'auto' }}>
        <Box sx={{ minWidth: 780 }}>
          {/* Header row */}
          <Box sx={{
            display: 'grid',
            gridTemplateColumns: '180px minmax(180px, 1fr) 50px 50px repeat(9, 40px) 80px',
            gap: 0, alignItems: 'center',
            position: 'sticky', top: 0, zIndex: 1,
            bgcolor: 'var(--bg-page)',
            borderBottom: '1px solid var(--rule)',
            py: 1,
          }}>
            <SortableHeader label="spec id" active={sortKey === 'id'} dir={sortDir} onClick={() => handleSort('id')} />
            <SortableHeader label="title" active={sortKey === 'title'} dir={sortDir} onClick={() => handleSort('title')} />
            <HeaderCell>#</HeaderCell>
            <SortableHeader label="avg" active={sortKey === 'avg_score'} dir={sortDir} onClick={() => handleSort('avg_score')} center />
            {LIBRARIES.map(lib => (
              <HeaderCell key={lib} center>{LIB_ABBREV[lib] ?? lib.slice(0, 3)}</HeaderCell>
            ))}
            <SortableHeader label="updated" active={sortKey === 'updated'} dir={sortDir} onClick={() => handleSort('updated')} />
          </Box>

          {/* Body rows */}
          {filteredSpecs.map(spec => {
            const implCount = countImpls(spec);
            return (
              <Box
                key={spec.id}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '180px minmax(180px, 1fr) 50px 50px repeat(9, 40px) 80px',
                  gap: 0, alignItems: 'center', py: 0.5,
                  borderBottom: '1px solid var(--rule)',
                  '&:hover': { bgcolor: 'var(--bg-surface)' },
                }}
              >
                <Link
                  component={RouterLink}
                  to={specPath(spec.id)}
                  sx={{
                    fontFamily: typography.fontFamily, fontSize: fontSize.xs,
                    color: colors.primary, textDecoration: 'none',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {spec.id}
                </Link>
                <Typography sx={{
                  fontFamily: typography.fontFamily, fontSize: fontSize.xs,
                  color: semanticColors.labelText,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', pr: 1,
                }}>
                  {spec.title}
                </Typography>
                <Typography sx={{
                  fontFamily: typography.fontFamily, fontSize: fontSize.xs, fontWeight: 600,
                  color: implCount === 9 ? colors.success : implCount > 0 ? semanticColors.mutedText : 'var(--ink-muted)',
                  textAlign: 'center',
                }}>
                  {implCount}/9
                </Typography>
                <Typography sx={{
                  fontFamily: typography.fontFamily, fontSize: fontSize.xs, fontWeight: 600,
                  color: scoreColor(spec.avg_score), textAlign: 'center',
                }}>
                  {spec.avg_score !== null ? spec.avg_score.toFixed(1) : '—'}
                </Typography>
                {LIBRARIES.map(lib => {
                  const score = spec[lib as keyof SpecStatus] as number | null;
                  if (score === null) {
                    return (
                      <Box key={lib} sx={{ textAlign: 'center', fontFamily: typography.fontFamily, fontSize: fontSize.xs, color: 'var(--ink-muted)' }}>
                        —
                      </Box>
                    );
                  }
                  return (
                    <Link
                      key={lib}
                      component={RouterLink}
                      to={specPath(spec.id, 'python', lib)}
                      sx={{
                        textAlign: 'center', textDecoration: 'none',
                        fontFamily: typography.fontFamily, fontSize: fontSize.xs, fontWeight: 600,
                        color: scoreColor(score),
                        '&:hover': { opacity: 0.7 },
                      }}
                    >
                      {Math.round(score)}
                    </Link>
                  );
                })}
                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText }}>
                  {spec.updated ? formatDateShort(spec.updated) : '—'}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>

      {/* Mobile: card list */}
      <Box sx={{ display: { xs: 'flex', md: 'none' }, flexDirection: 'column', gap: 1.5 }}>
        {filteredSpecs.map(spec => (
          <Box
            key={spec.id}
            sx={{
              border: '1px solid var(--rule)', borderRadius: 1, p: 1.5,
              display: 'flex', flexDirection: 'column', gap: 1,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
              <Link
                component={RouterLink}
                to={specPath(spec.id)}
                sx={{
                  flex: 1, fontFamily: typography.fontFamily, fontSize: fontSize.sm,
                  color: 'var(--ink)', textDecoration: 'none', fontWeight: 500,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  '&:hover': { color: colors.primary },
                }}
              >
                {spec.title}
              </Link>
              <Typography sx={{
                fontFamily: typography.fontFamily, fontSize: fontSize.xs,
                color: scoreColor(spec.avg_score), fontWeight: 600, flexShrink: 0,
              }}>
                avg {spec.avg_score !== null ? spec.avg_score.toFixed(0) : '—'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {LIBRARIES.map(lib => {
                const score = spec[lib as keyof SpecStatus] as number | null;
                const missing = score === null;
                const abbrev = LIB_ABBREV[lib] ?? lib.slice(0, 3);
                const commonSx = {
                  display: 'inline-flex', alignItems: 'center', gap: 0.5,
                  px: 0.75, py: 0.25, borderRadius: 0.5,
                  fontFamily: typography.fontFamily, fontSize: fontSize.xxs, fontWeight: 600,
                  textDecoration: 'none',
                  bgcolor: missing ? 'var(--bg-elevated)' : `${scoreColor(score)}22`,
                  color: missing ? 'var(--ink-muted)' : scoreColor(score),
                };
                if (missing) {
                  return (
                    <Box key={lib} sx={commonSx}>
                      <Box component="span">{abbrev}</Box>
                      <Box component="span">—</Box>
                    </Box>
                  );
                }
                return (
                  <Link
                    key={lib}
                    component={RouterLink}
                    to={specPath(spec.id, 'python', lib)}
                    sx={{ ...commonSx, '&:hover': { opacity: 0.75 } }}
                  >
                    <Box component="span">{abbrev}</Box>
                    <Box component="span">{Math.round(score)}</Box>
                  </Link>
                );
              })}
            </Box>
            <Box sx={{ display: 'flex', gap: 1, fontFamily: typography.fontFamily, fontSize: fontSize.xxs, color: semanticColors.mutedText }}>
              <Box component="span" sx={{ color: colors.primary }}>{spec.id}</Box>
              <Box component="span">·</Box>
              <Box component="span">{spec.updated ? timeAgo(spec.updated) : 'no activity'}</Box>
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

// ============================================================================
// Sortable header helpers
// ============================================================================

function HeaderCell({ children, center }: { children: React.ReactNode; center?: boolean }) {
  return (
    <Typography sx={{
      fontFamily: typography.fontFamily, fontSize: fontSize.xs, fontWeight: 600,
      color: 'var(--ink-soft)', textAlign: center ? 'center' : 'left',
    }}>
      {children}
    </Typography>
  );
}

function SortableHeader({
  label, active, dir, onClick, center,
}: { label: string; active: boolean; dir: SortDir; onClick: () => void; center?: boolean }) {
  return (
    <Box
      component="button"
      type="button"
      onClick={onClick}
      sx={{
        background: 'none', border: 'none', p: 0, cursor: 'pointer',
        fontFamily: typography.fontFamily, fontSize: fontSize.xs, fontWeight: 600,
        color: active ? colors.primary : 'var(--ink-soft)',
        textAlign: center ? 'center' : 'left',
        display: 'flex', alignItems: 'center', gap: 0.25,
        justifyContent: center ? 'center' : 'flex-start',
        '&:hover': { color: colors.primaryDark },
      }}
    >
      {label}
      {active && (
        <Box component="span" sx={{ fontSize: fontSize.micro }}>
          {dir === 'asc' ? '▲' : '▼'}
        </Box>
      )}
    </Box>
  );
}
