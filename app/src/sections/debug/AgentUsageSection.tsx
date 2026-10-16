/**
 * The debug page's "agent usage" section: what the agent chat's content-free
 * telemetry adds up to over the last 7 or 30 days (`GET /debug/agent-usage`).
 *
 * - Four tiles: sessions, plots shipped, the kept rate (sessions with a shipped
 *   plot whose user copied or downloaded a result after the last run and gave
 *   no thumbs_down or bug; a saved session alone is no keep) and the repair rate
 *   (runs that needed more than one round), each rate with its counts ("5 of
 *   12"); a rate without a base reads `—`.
 * - Three short ranked lists: the specs, the data formats and the refusal
 *   codes seen most often.
 * - BigQuery not set up yet (`not_configured`), a failed query (`unavailable`)
 *   and a window without sessions are one muted line each. A failed request or
 *   an answer the page cannot read is the `unavailable` line too: the section
 *   never breaks the rest of the page, and never reloads it for Cloudflare
 *   Access (the page's own `/debug/status` call owns that).
 */

import { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import { timeAgo } from 'src/sections/debug/format';
import { debugControlSx, listMutedSx, listTextSx } from 'src/sections/debug/styles';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

/** The windows the endpoint takes, in days. */
const USAGE_WINDOWS = [7, 30] as const;
type UsageWindow = (typeof USAGE_WINDOWS)[number];

export interface UsageCount {
  key: string;
  count: number;
}

/** The answer of `GET /debug/agent-usage?days=N`. */
export interface AgentUsage {
  status: 'ok' | 'not_configured' | 'unavailable';
  days: number;
  sessions: number;
  plots_shipped: number;
  kept_rate: number | null;
  /** Sessions kept (a copy or download after the last run, no thumbs_down or bug; a save alone is no keep). */
  kept_sessions: number;
  /** Sessions with a shipped plot: the kept rate's base. */
  shipped_sessions: number;
  repair_rate: number | null;
  repaired_runs: number;
  /** Pipeline runs that started: the repair rate's base. */
  runs: number;
  top_specs: UsageCount[];
  top_formats: UsageCount[];
  top_refusals: UsageCount[];
  generated_at: string | null;
}

/** The longest list the endpoint sends; anything beyond is dropped. */
const MAX_TOP = 5;

const STATUSES = new Set<string>(['ok', 'not_configured', 'unavailable']);

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

const rate = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;

const topList = (value: unknown): UsageCount[] =>
  Array.isArray(value)
    ? value
        .filter(
          (item): item is UsageCount =>
            !!item &&
            typeof item === 'object' &&
            typeof (item as UsageCount).key === 'string' &&
            typeof (item as UsageCount).count === 'number'
        )
        .slice(0, MAX_TOP)
        .map(item => ({ key: item.key, count: count(item.count) }))
    : [];

/** The answer as the section reads it; `null` for one without a known status. */
function readAgentUsage(body: unknown): AgentUsage | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (typeof record.status !== 'string' || !STATUSES.has(record.status)) return null;
  return {
    status: record.status as AgentUsage['status'],
    days: count(record.days),
    sessions: count(record.sessions),
    plots_shipped: count(record.plots_shipped),
    kept_rate: rate(record.kept_rate),
    kept_sessions: count(record.kept_sessions),
    shipped_sessions: count(record.shipped_sessions),
    repair_rate: rate(record.repair_rate),
    repaired_runs: count(record.repaired_runs),
    runs: count(record.runs),
    top_specs: topList(record.top_specs),
    top_formats: topList(record.top_formats),
    top_refusals: topList(record.top_refusals),
    generated_at: typeof record.generated_at === 'string' ? record.generated_at : null,
  };
}

const percent = (value: number | null): string =>
  value === null ? '—' : `${Math.round(value * 100)}%`;

/** The counts behind a rate ("1 of 3"), so a percentage of three sessions reads as what it is. */
const ofTotal = (part: number, total: number): string | undefined =>
  total > 0 ? `${part.toLocaleString('en-US')} of ${total.toLocaleString('en-US')}` : undefined;

const EMPTY_TEXT: Record<'not_configured' | 'unavailable' | 'empty', string> = {
  not_configured: 'BigQuery telemetry is not configured yet',
  unavailable: 'usage data unavailable right now',
  empty: 'no sessions in this window',
};

export interface AgentUsageSectionProps {
  /** The admin token of the page (`X-Admin-Token`), or `''` behind Cloudflare Access. */
  token: string;
  /** The page's reload count: a change fetches the numbers again. */
  reloadCounter: number;
}

interface UsageState {
  /** The token, reload count and window the answer belongs to. */
  key: string;
  /** `null` when the request failed or the answer was unreadable. */
  usage: AgentUsage | null;
}

export function AgentUsageSection({ token, reloadCounter }: AgentUsageSectionProps) {
  const [days, setDays] = useState<UsageWindow>(7);
  const key = `${token}\n${reloadCounter}\n${days}`;
  const [answer, setAnswer] = useState<UsageState | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchWithAuth(`${DEBUG_API_URL}/debug/agent-usage?days=${days}`, token)
      .then(async response => (response.ok ? readAgentUsage(await response.json()) : null))
      .catch(() => null)
      .then(usage => {
        if (!cancelled) setAnswer({ key, usage });
      });
    return () => {
      cancelled = true;
    };
  }, [token, days, key]);

  const current = answer && answer.key === key ? answer : null;
  const usage = current?.usage ?? null;
  const empty: keyof typeof EMPTY_TEXT | null = !current
    ? null
    : !usage || usage.status === 'unavailable'
      ? 'unavailable'
      : usage.status === 'not_configured'
        ? 'not_configured'
        : usage.sessions === 0 && usage.plots_shipped === 0
          ? 'empty'
          : null;

  return (
    <Box component="section" aria-label="Agent usage section" sx={{ mb: 4 }}>
      <Box sx={{ mt: 4, display: 'flex', alignItems: 'center', columnGap: 2, flexWrap: 'wrap' }}>
        <SectionHeader prompt="❯" title={<em>agent usage</em>} />
        <Box
          role="group"
          aria-label="Usage window"
          sx={{ ml: 'auto', mb: { xs: 2, sm: 0 }, display: 'flex', gap: 0.5 }}
        >
          {USAGE_WINDOWS.map(span => {
            const active = span === days;
            return (
              <Box
                key={span}
                component="button"
                type="button"
                aria-pressed={active}
                onClick={() => setDays(span)}
                sx={{
                  ...debugControlSx,
                  cursor: 'pointer',
                  color: active ? 'var(--ink)' : 'var(--ink-soft)',
                  fontWeight: active ? 600 : 400,
                  borderColor: active ? colors.primary : 'var(--rule)',
                }}
              >
                {span}d
              </Box>
            );
          })}
        </Box>
      </Box>
      <Typography sx={{ ...listMutedSx, mb: 1.5 }}>
        content-free telemetry · last {days} days
        {usage?.generated_at ? ` · generated ${timeAgo(usage.generated_at)}` : ''}
      </Typography>

      {!current ? (
        <Typography sx={{ ...listMutedSx, py: 1 }}>loading usage…</Typography>
      ) : empty || !usage ? (
        <Typography data-testid="agent-usage-empty" sx={{ ...listMutedSx, py: 1 }}>
          {EMPTY_TEXT[empty ?? 'unavailable']}
        </Typography>
      ) : (
        <>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
              gap: 2,
              mb: 2,
            }}
          >
            <UsageTile label="sessions" value={usage.sessions.toLocaleString('en-US')} />
            <UsageTile label="plots shipped" value={usage.plots_shipped.toLocaleString('en-US')} />
            <UsageTile
              label="kept rate"
              value={percent(usage.kept_rate)}
              detail={ofTotal(usage.kept_sessions, usage.shipped_sessions)}
            />
            <UsageTile
              label="repair rate"
              value={percent(usage.repair_rate)}
              detail={ofTotal(usage.repaired_runs, usage.runs)}
            />
          </Box>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
              gap: 2,
            }}
          >
            <UsageTopList title="top specs" items={usage.top_specs} />
            <UsageTopList title="top formats" items={usage.top_formats} />
            <UsageTopList title="top refusal codes" items={usage.top_refusals} />
          </Box>
        </>
      )}
    </Box>
  );
}

/** One KPI tile, as the page's own KPI grid draws them. */
function UsageTile({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <Box
      role="group"
      aria-label={label}
      sx={{ textAlign: 'center', p: 2, border: '1px solid var(--rule)', borderRadius: 1 }}
    >
      <Typography
        sx={{
          fontFamily: typography.serif,
          fontSize: '2rem',
          fontWeight: 300,
          color: 'var(--ink)',
          lineHeight: 1.2,
        }}
      >
        {value}
      </Typography>
      {detail && <Typography sx={{ ...listMutedSx, mt: 0.25 }}>{detail}</Typography>}
      <Typography sx={{ ...listMutedSx, mt: 0.5 }}>{label}</Typography>
    </Box>
  );
}

/** A short ranked list: the count, then the key. */
function UsageTopList({ title, items }: { title: string; items: UsageCount[] }) {
  return (
    <Box
      role="group"
      aria-label={title}
      sx={{ border: '1px solid var(--rule)', borderRadius: 1, p: 1.5, minWidth: 0 }}
    >
      <Typography sx={{ ...listTextSx, fontWeight: 600, color: 'var(--ink-soft)', mb: 1 }}>
        {title}
      </Typography>
      {items.length === 0 ? (
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xxs,
            color: semanticColors.mutedText,
          }}
        >
          none in this window
        </Typography>
      ) : (
        <Box component="ol" sx={{ m: 0, p: 0, listStyle: 'none' }}>
          {items.map(item => (
            <Box
              component="li"
              key={item.key}
              sx={{
                display: 'grid',
                gridTemplateColumns: '32px 1fr',
                gap: 1,
                alignItems: 'baseline',
                py: 0.4,
                borderBottom: '1px solid var(--rule)',
                '&:last-of-type': { borderBottom: 'none' },
              }}
            >
              <Typography
                component="span"
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  color: colors.primary,
                  fontWeight: 600,
                  textAlign: 'right',
                }}
              >
                {item.count}
              </Typography>
              <Typography
                component="span"
                sx={{
                  ...listTextSx,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {item.key}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
