import { useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DEBUG_API_URL, LIBRARIES } from 'src/constants';
import { useAnalytics } from 'src/hooks';
import { fetchWithAuth } from 'src/lib/api';
import { AgentCasesSection } from 'src/sections/debug/AgentCasesSection';
import { AgentUsageSection } from 'src/sections/debug/AgentUsageSection';
import { CommonWeaknesses } from 'src/sections/debug/CommonWeaknesses';
import type { FeedbackMessageFilter } from 'src/sections/debug/constants';
import { DailyActivityChart } from 'src/sections/debug/DailyActivityChart';
import { FeedbackSection } from 'src/sections/debug/FeedbackSection';
import { KPIGrid } from 'src/sections/debug/KPIGrid';
import { LibraryCoverage } from 'src/sections/debug/LibraryCoverage';
import { ProblemAreas } from 'src/sections/debug/ProblemAreas';
import { RecentActivity } from 'src/sections/debug/RecentActivity';
import { SpecMatrix, SpecStatus } from 'src/sections/debug/SpecMatrix';
import { debugControlSx } from 'src/sections/debug/styles';
import { SystemHealthRow } from 'src/sections/debug/SystemHealthRow';
import { colors, fontSize, semanticColors, typography } from 'src/theme';
import {
  clearAccessReloadGuard,
  clearAdminToken,
  readAdminToken,
  reloadOnceForAccess,
  setAdminHint,
  writeAdminToken,
} from 'src/utils/adminAuth';

// ============================================================================
// Types
// ============================================================================

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

interface RecentActivityData {
  spec_id: string;
  spec_title: string;
  library_id: string;
  language_id: string;
  quality_score: number | null;
  generated_by: string | null;
  updated: string;
}

interface WeaknessCount {
  text: string;
  count: number;
}

interface FeedbackTopPage {
  path: string;
  count: number;
  last_seen: string | null;
}

export type FeedbackStatus = 'new' | 'in_progress' | 'done' | 'wont_solve';

// "" → all statuses, "open" → new + in_progress (server-side pseudo-filter).
// Default view shows the open queue so resolved entries don't drown out triage.
const DEFAULT_MESSAGE_FILTER: FeedbackMessageFilter = 'open';

interface FeedbackMessageItem {
  id: string;
  message: string;
  reaction: string | null;
  contact: string | null;
  path: string | null;
  spec_id: string | null;
  viewport: string | null;
  status: FeedbackStatus;
  created_at: string;
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
  recent_activity: RecentActivityData[];
  common_weaknesses: WeaknessCount[];
  system: SystemHealth;
  specs: SpecStatus[];
}

type SortKey = keyof SpecStatus | 'coverage';
type SortDir = 'asc' | 'desc';

// ============================================================================
// Helpers
// ============================================================================

const LOW_SCORE_THRESHOLD = 90;

// ============================================================================
// Component
// ============================================================================

const PING_INTERVAL_MS = 2000;
const PING_HISTORY = 30;

// Admin auth for /debug endpoints (require_admin in api/routers/debug.py).
// Two paths:
//   - Cloudflare Access cookie set on .anyplot.ai → forwarded as Cf-Access-Jwt-Assertion
//     to api.anyplot.ai. credentials: 'include' is required for the cookie to
//     travel cross-origin to the API.
//   - X-Admin-Token header as a fallback (CI, break-glass, local dev). Stored
//     in sessionStorage so it survives reloads of the same tab without
//     persisting across browser sessions (src/utils/adminAuth.ts).
// A 200 from /debug/status also sets the admin hint that lets the plot page
// show the agent chat's `.adapt()` button; a refusal clears it.

export function DebugPage() {
  const { trackPageview } = useAnalytics();
  useEffect(() => {
    trackPageview('/debug');
  }, [trackPageview]);

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
  const [prevFetchKey, setPrevFetchKey] = useState({ adminToken, reloadCounter });

  const [topThumbsUp, setTopThumbsUp] = useState<FeedbackTopPage[]>([]);
  const [topThumbsDown, setTopThumbsDown] = useState<FeedbackTopPage[]>([]);
  const [feedbackMessages, setFeedbackMessages] = useState<FeedbackMessageItem[]>([]);
  const [feedbackStatusFilter, setFeedbackStatusFilter] =
    useState<FeedbackMessageFilter>(DEFAULT_MESSAGE_FILTER);

  // React 19 "adjust state on prop change": reset loading/error when fetch deps change.
  if (prevFetchKey.adminToken !== adminToken || prevFetchKey.reloadCounter !== reloadCounter) {
    setPrevFetchKey({ adminToken, reloadCounter });
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    fetchWithAuth(`${DEBUG_API_URL}/debug/status`, adminToken)
      .then(async r => {
        // Reaching here means the fetch promise resolved (the response may
        // still be 401/403/503 — those are handled below). Clear the one-shot
        // reload guard so a future cross-origin CF Access redirect can
        // re-trigger the bootstrap.
        clearAccessReloadGuard();
        // 403 is the Cloudflare Access JWT path's denial: a signed-in Google
        // account that isn't on the admin_allowed_emails allow-list. Surface
        // it on the auth-required screen with the server's message so the
        // user knows to sign in with a different account or ask for access.
        if (r.status === 401 || r.status === 403 || r.status === 503) {
          setAdminHint(false);
          setAuthRequired(true);
          if (r.status === 403) {
            const body = await r.json().catch(() => ({}));
            throw new Error(body?.message || 'this account is not authorized for /debug');
          }
          throw new Error(
            r.status === 503 ? 'admin auth not configured on server' : 'admin token required'
          );
        }
        if (!r.ok) throw new Error(`${r.status}`);
        setAdminHint(true);
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
        // to Google login. The sessionStorage guard keeps this from looping if
        // the second load ALSO fails (e.g. wrong allow-list); the agent chat
        // page shares it (src/utils/adminAuth.ts).
        if (e instanceof TypeError && reloadOnceForAccess()) return;
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
        const r = await fetchWithAuth(`${DEBUG_API_URL}/debug/ping`, adminToken);
        const totalMs = performance.now() - started;
        if (!r.ok) throw new Error(`${r.status}`);
        const json: { database_connected: boolean } = await r.json();
        if (cancelled) return;
        setPings(prev => [
          ...prev.slice(-(PING_HISTORY - 1)),
          { ms: totalMs, ok: json.database_connected },
        ]);
      } catch {
        if (cancelled) return;
        const totalMs = performance.now() - started;
        setPings(prev => [...prev.slice(-(PING_HISTORY - 1)), { ms: totalMs, ok: false }]);
      }
    };
    tick();
    const id = setInterval(tick, PING_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [adminToken, authRequired]);

  useEffect(() => {
    if (authRequired) return;
    let cancelled = false;
    const qs = feedbackStatusFilter ? `?status=${feedbackStatusFilter}&limit=50` : '?limit=50';
    Promise.all([
      fetchWithAuth(
        `${DEBUG_API_URL}/debug/feedback/top?reaction=thumbs_up&limit=15`,
        adminToken
      ).then(r => (r.ok ? (r.json() as Promise<FeedbackTopPage[]>) : [])),
      fetchWithAuth(
        `${DEBUG_API_URL}/debug/feedback/top?reaction=thumbs_down&limit=15`,
        adminToken
      ).then(r => (r.ok ? (r.json() as Promise<FeedbackTopPage[]>) : [])),
      fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/messages${qs}`, adminToken).then(r =>
        r.ok ? (r.json() as Promise<FeedbackMessageItem[]>) : []
      ),
    ])
      .then(([up, down, msgs]) => {
        if (cancelled) return;
        setTopThumbsUp(Array.isArray(up) ? up : []);
        setTopThumbsDown(Array.isArray(down) ? down : []);
        setFeedbackMessages(Array.isArray(msgs) ? msgs : []);
      })
      .catch(() => {
        /* /debug/status useEffect already surfaces auth/network errors */
      });
    return () => {
      cancelled = true;
    };
  }, [adminToken, authRequired, reloadCounter, feedbackStatusFilter]);

  const updateFeedbackStatus = async (id: string, newStatus: string) => {
    // Optimistic update — revert on failure so the dropdown stays truthful.
    const prev = feedbackMessages;
    setFeedbackMessages(
      prev.map(m => (m.id === id ? { ...m, status: newStatus as FeedbackStatus } : m))
    );
    try {
      const r = await fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/${id}`, adminToken, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      if (!r.ok) throw new Error(`${r.status}`);
    } catch {
      setFeedbackMessages(prev);
    }
  };

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
      filtered = filtered.filter(
        s => s.id.toLowerCase().includes(q) || s.title.toLowerCase().includes(q)
      );
    }
    if (showIncomplete) filtered = filtered.filter(s => countImpls(s) < LIBRARIES.length);
    if (showLowScores) filtered = filtered.filter(hasLowScore);
    if (missingLibrary)
      filtered = filtered.filter(s => s[missingLibrary as keyof SpecStatus] === null);

    filtered.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'updated':
          cmp = (a.updated || '').localeCompare(b.updated || '');
          break;
        case 'id':
          cmp = a.id.localeCompare(b.id);
          break;
        case 'title':
          cmp = a.title.localeCompare(b.title);
          break;
        case 'avg_score':
          cmp = (a.avg_score ?? 0) - (b.avg_score ?? 0);
          break;
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
        <title>debug | anyplot.ai</title>
        <SectionHeader prompt="❯" title={<em>debug · admin auth</em>} />
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: semanticColors.mutedText,
            mb: 2,
          }}
        >
          {error || 'sign in via your browser session, or paste an admin token as a fallback.'}
        </Typography>
        <Box
          component="form"
          onSubmit={handleTokenSubmit}
          sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
        >
          <Box
            component="input"
            type="password"
            autoFocus
            placeholder="Admin token (fallback)"
            value={tokenInput}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTokenInput(e.target.value)}
            sx={debugControlSx}
          />
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Box
              component="button"
              type="submit"
              sx={{
                ...debugControlSx,
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
                sx={{ ...debugControlSx, cursor: 'pointer' }}
              >
                clear stored token
              </Box>
            )}
          </Box>
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: fontSize.xxs,
              color: semanticColors.mutedText,
              mt: 1,
            }}
          >
            stored in sessionStorage — clears when this tab closes.
          </Typography>
        </Box>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <title>debug | anyplot.ai</title>
        <Typography sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText }}>
          loading debug data...
        </Typography>
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <title>debug | anyplot.ai</title>
        <Typography sx={{ fontFamily: typography.fontFamily, color: colors.error }}>
          failed to load{error ? `: ${error}` : ''}
        </Typography>
      </Box>
    );
  }

  // Derived KPIs
  const totalImplsWithScore = data.library_stats.reduce(
    (acc, l) => acc + (l.avg_score !== null ? l.impl_count : 0),
    0
  );
  const weightedScoreSum = data.library_stats.reduce(
    (acc, l) => acc + (l.avg_score !== null ? l.avg_score * l.impl_count : 0),
    0
  );
  const avgQuality = totalImplsWithScore > 0 ? weightedScoreSum / totalImplsWithScore : null;

  const kpis: Array<{ label: string; value: number | null; suffix?: string }> = [
    { label: 'specs', value: data.total_specs },
    { label: 'impls', value: data.total_implementations },
    { label: 'coverage', value: data.coverage_percent, suffix: '%' },
    { label: 'avg quality', value: avgQuality !== null ? Math.round(avgQuality * 10) / 10 : null },
    { label: 'low score', value: data.low_score_specs.length },
    { label: 'stale specs', value: data.oldest_specs.length },
  ];

  return (
    <Box sx={{ pt: { xs: 2, md: 3 }, pb: 4 }}>
      <title>debug | anyplot.ai</title>
      {/* Header */}
      <SectionHeader prompt="❯" title={<em>debug</em>} />

      <SystemHealthRow pings={pings} systemData={data.system} pingHistory={PING_HISTORY} />
      <KPIGrid kpis={kpis} />
      <DailyActivityChart data={data.daily_impls} />
      <LibraryCoverage stats={data.library_stats} />
      <RecentActivity activity={data.recent_activity} />
      <CommonWeaknesses weaknesses={data.common_weaknesses} />
      <ProblemAreas
        lowScoreThreshold={LOW_SCORE_THRESHOLD}
        lowScoreSpecs={data.low_score_specs}
        missingPreviewSpecs={data.missing_preview_specs}
        missingTagsSpecs={data.missing_tags_specs}
        oldestSpecs={data.oldest_specs}
      />
      <FeedbackSection
        topThumbsUp={topThumbsUp}
        topThumbsDown={topThumbsDown}
        feedbackStatusFilter={feedbackStatusFilter}
        setFeedbackStatusFilter={setFeedbackStatusFilter}
        feedbackMessages={feedbackMessages}
        handleStatusChange={updateFeedbackStatus}
      />

      {/* Agent usage: the agent chat's content-free telemetry, 7 or 30 days */}
      <AgentUsageSection token={adminToken} reloadCounter={reloadCounter} />

      {/* Agent cases: the triage of the agent chat's quick feedback */}
      <AgentCasesSection token={adminToken} reloadCounter={reloadCounter} />

      <SpecMatrix
        searchText={searchText}
        setSearchText={setSearchText}
        showIncomplete={showIncomplete}
        setShowIncomplete={setShowIncomplete}
        showLowScores={showLowScores}
        setShowLowScores={setShowLowScores}
        missingLibrary={missingLibrary}
        setMissingLibrary={setMissingLibrary}
        filteredSpecs={filteredSpecs}
        totalSpecs={data.total_specs}
        sortCol={sortKey}
        sortDir={sortDir}
        handleSort={handleSort}
      />
    </Box>
  );
}

// ============================================================================
