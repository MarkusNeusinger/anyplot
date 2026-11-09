/**
 * The agent usage section's two views of the day, below the 7- and 30-day tiles:
 *
 * - `AgentTodayLine`: today so far, live from the agents service's usage book
 *   (`GET /debug/agent/budget`): the service's spend against its day budget, in
 *   USD and weighted tokens, and how many users are at their own limits. The
 *   counts live in the instance's memory, so the line says since when they
 *   count and that a restart starts them again.
 * - `AgentDailyTable`: the last 14 UTC days from the BigQuery telemetry
 *   (`GET /debug/agent-usage/daily`), newest first: new chats, plots shipped,
 *   the cost (live, and the admin fan-out's apart), the limit refusals by code
 *   and the run queue's 95th-percentile wait, `—` on a day before the field.
 *
 * Each fetches on its own and fails to one muted line, like the section above.
 */

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { DEBUG_API_URL } from 'src/constants';
import { type AgentBudget, budgetShare, countsOf, LIMIT_KINDS, readBudget } from 'src/lib/agent';
import { localClock } from 'src/sections/agent-chat/messages';
import { formatUsd, formatUtc, timeAgo } from 'src/sections/debug/format';
import { listMutedSx, listTextSx, tableCellSx, tableHeadSx } from 'src/sections/debug/styles';
import { useAnswer } from 'src/sections/debug/useAnswer';
import { colors } from 'src/theme';

// ============================================================================
// Answers
// ============================================================================

// The live answer of `GET /debug/agent/budget` (`AgentBudget`, `readBudget`) is the chat's too,
// whose admin meters show the same share: both live in `src/lib/agent.ts`.

/** The refusal codes the per-day table counts, in its order (`api/agent_usage.py` `LIMIT_CODES`). */
const LIMIT_CODES = [
  'service_paused',
  'budget',
  'daily_limit',
  'rate_limited',
  'run_limit',
  'capacity',
] as const;

export interface UsageDay {
  date: string;
  sessions: number;
  plots_shipped: number;
  cost_usd: number;
  fanout_cost_usd: number;
  unpriced_calls: number;
  limit_hits: Record<string, number>;
  queue_wait_p95_ms: number | null;
  queue_waits: number;
}

/** The answer of `GET /debug/agent-usage/daily`. */
export interface AgentUsageDaily {
  status: 'ok' | 'not_configured' | 'unavailable';
  rows: UsageDay[];
  generated_at: string | null;
}

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

const amount = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;

const STATUSES = new Set<string>(['ok', 'not_configured', 'unavailable']);

/** The per-day answer as the table reads it; `null` for one without a known status. */
function readDaily(body: unknown): AgentUsageDaily | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  if (typeof record.status !== 'string' || !STATUSES.has(record.status)) return null;
  const rows = Array.isArray(record.rows) ? record.rows : [];
  return {
    status: record.status as AgentUsageDaily['status'],
    rows: rows
      .filter(
        (row): row is Record<string, unknown> =>
          !!row && typeof row === 'object' && typeof (row as UsageDay).date === 'string'
      )
      .map(row => {
        const wait = row.queue_wait_p95_ms;
        return {
          date: row.date as string,
          sessions: count(row.sessions),
          plots_shipped: count(row.plots_shipped),
          cost_usd: amount(row.cost_usd) ?? 0,
          fanout_cost_usd: amount(row.fanout_cost_usd) ?? 0,
          unpriced_calls: count(row.unpriced_calls),
          limit_hits: countsOf(row.limit_hits, LIMIT_CODES),
          queue_wait_p95_ms: typeof wait === 'number' && wait >= 0 ? wait : null,
          queue_waits: count(row.queue_waits),
        };
      }),
    generated_at: typeof record.generated_at === 'string' ? record.generated_at : null,
  };
}

// ============================================================================
// Formatting
// ============================================================================

const millions = (tokens: number): string => `${(tokens / 1e6).toFixed(1)} M`;

/** The time of day of a UTC instant, `14:05 UTC`. */
const utcClock = (iso: string): string => `${new Date(iso).toISOString().slice(11, 16)} UTC`;

const plural = (value: number, noun: string): string =>
  `${value.toLocaleString('en-US')} ${noun}${value === 1 ? '' : 's'}`;

/** The day caps users are at, those with any: `tokens 1, runs 2`. */
function limitBreakdown(limits: Record<string, number>): string {
  return LIMIT_KINDS.filter(kind => limits[kind] > 0)
    .map(kind => `${kind.replace('_', ' ')} ${limits[kind]}`)
    .join(', ');
}

// ============================================================================
// Today, live
// ============================================================================

export interface DayViewProps {
  /** The admin token of the page (`X-Admin-Token`), or `''` behind Cloudflare Access. */
  token: string;
  /** The page's reload count: a change fetches again. */
  reloadCounter: number;
}

const subheadSx = {
  ...listTextSx,
  fontWeight: 600,
  color: 'var(--ink-soft)',
  mt: 3,
  mb: 0.75,
} as const;

export function AgentTodayLine({ token, reloadCounter }: DayViewProps) {
  const budget = useAnswer(`${DEBUG_API_URL}/debug/agent/budget`, token, reloadCounter, readBudget);

  return (
    <Box role="group" aria-label="Today, live">
      <Typography sx={subheadSx}>today · live from the agents service</Typography>
      {budget === undefined ? (
        <Typography sx={listMutedSx}>loading today…</Typography>
      ) : budget === null ? (
        <Typography data-testid="agent-today-empty" sx={listMutedSx}>
          live numbers unavailable: the agents service did not answer
        </Typography>
      ) : (
        <TodayText budget={budget} />
      )}
    </Box>
  );
}

function TodayText({ budget }: { budget: AgentBudget }) {
  const share = budgetShare(budget);
  const spend =
    budget.usd !== null && budget.budget_usd !== null
      ? `${formatUsd(budget.usd)} of ${formatUsd(budget.budget_usd)}`
      : `${millions(budget.tokens)} of ${millions(budget.budget_tokens)} weighted tokens`;
  const tokens =
    budget.usd !== null && budget.budget_usd !== null
      ? ` (${millions(budget.tokens)} of ${millions(budget.budget_tokens)} weighted tokens${share !== null ? `, ${share}%` : ''})`
      : '';
  const breakdown = limitBreakdown(budget.limits);
  const startedToday = budget.since === budget.started_at;
  // UTC like the rest of the line, then the reader's own clock.
  const local = localClock(budget.resets_at);
  const resets = `${utcClock(budget.resets_at)}${local ? ` (${local} your time)` : ''}`;
  return (
    <>
      {budget.paused && (
        <Typography
          data-testid="agent-today-paused"
          sx={{
            ...listTextSx,
            borderLeft: `3px solid ${colors.warning}`,
            pl: 1,
            mb: 0.5,
          }}
        >
          paused · the day budget is spent: every turn gets service_paused until {resets}
        </Typography>
      )}
      <Typography data-testid="agent-today" sx={listTextSx}>
        today: {spend}
        {tokens} · {plural(budget.users, 'user')}, {budget.users_at_limit} at their own limit
        {breakdown ? ` (${breakdown})` : ''}
      </Typography>
      <Typography sx={{ ...listMutedSx, mt: 0.25 }}>
        {startedToday
          ? `counted since ${utcClock(budget.since)}, when this instance started`
          : `counted since 00:00 UTC; this instance has run since ${formatUtc(budget.started_at)}`}
        {' · '}a redeploy or a scale to zero starts the counts again · the new day starts at{' '}
        {resets}
      </Typography>
    </>
  );
}

// ============================================================================
// The last 14 days
// ============================================================================

const DAILY_EMPTY: Record<'not_configured' | 'unavailable', string> = {
  not_configured: 'BigQuery telemetry is not configured yet',
  unavailable: 'per-day numbers unavailable right now',
};

const COLUMNS = [
  'day (UTC)',
  'new chats',
  'plots',
  'cost',
  'fan-out',
  'limit hits',
  'p95 queue wait',
] as const;

export function AgentDailyTable({ token, reloadCounter }: DayViewProps) {
  const daily = useAnswer(
    `${DEBUG_API_URL}/debug/agent-usage/daily`,
    token,
    reloadCounter,
    readDaily
  );
  const empty =
    daily === null || daily?.status === 'unavailable'
      ? 'unavailable'
      : daily?.status === 'not_configured'
        ? 'not_configured'
        : null;

  return (
    <Box role="group" aria-label="Per day">
      <Typography sx={subheadSx}>per day · the last 14 UTC days, newest first</Typography>
      {daily === undefined ? (
        <Typography sx={listMutedSx}>loading the days…</Typography>
      ) : empty || !daily ? (
        <Typography data-testid="agent-daily-empty" sx={listMutedSx}>
          {DAILY_EMPTY[empty ?? 'unavailable']}
        </Typography>
      ) : (
        <>
          <Box sx={{ overflowX: 'auto' }}>
            <Box
              component="table"
              sx={{ borderCollapse: 'collapse', minWidth: 560, width: '100%' }}
            >
              <Box component="thead">
                <Box component="tr">
                  {COLUMNS.map((column, index) => (
                    <Box
                      component="th"
                      key={column}
                      scope="col"
                      sx={{
                        ...tableHeadSx,
                        textAlign: index === 0 || index === 5 ? 'left' : 'right',
                      }}
                    >
                      {column}
                    </Box>
                  ))}
                </Box>
              </Box>
              <Box component="tbody">
                {daily.rows.map((day, index) => (
                  <DayRow key={day.date} day={day} today={index === 0} />
                ))}
              </Box>
            </Box>
          </Box>
          <Typography sx={{ ...listMutedSx, mt: 0.75 }}>
            new chats: live sessions by the day of their first line · cost: list price, the
            fan-out's apart · limit hits: refusals and errors by code · — : no run on that day
            carried the queue wait yet
            {daily.generated_at ? ` · generated ${timeAgo(daily.generated_at)}` : ''}
          </Typography>
        </>
      )}
    </Box>
  );
}

function DayRow({ day, today }: { day: UsageDay; today: boolean }) {
  const hits = LIMIT_CODES.filter(code => day.limit_hits[code] > 0);
  const unpriced =
    day.unpriced_calls > 0 ? `${plural(day.unpriced_calls, 'model call')} without a price` : '';
  return (
    <Box component="tr">
      <Box component="th" scope="row" sx={{ ...tableCellSx, textAlign: 'left', fontWeight: 400 }}>
        {day.date}
        {today ? ' · so far' : ''}
      </Box>
      <Box component="td" sx={tableCellSx}>
        {day.sessions.toLocaleString('en-US')}
      </Box>
      <Box component="td" sx={tableCellSx}>
        {day.plots_shipped.toLocaleString('en-US')}
      </Box>
      <Box component="td" sx={tableCellSx} title={unpriced || undefined}>
        {formatUsd(day.cost_usd)}
        {unpriced ? '+' : ''}
      </Box>
      <Box component="td" sx={{ ...tableCellSx, color: 'var(--ink-soft)' }}>
        {formatUsd(day.fanout_cost_usd)}
      </Box>
      <Box component="td" sx={{ ...tableCellSx, textAlign: 'left' }}>
        {hits.length === 0 ? (
          <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
            0
          </Box>
        ) : (
          hits.map(code => `${code} ${day.limit_hits[code]}`).join(' · ')
        )}
      </Box>
      <Box
        component="td"
        sx={tableCellSx}
        title={day.queue_waits > 0 ? `of ${plural(day.queue_waits, 'run')}` : undefined}
      >
        {day.queue_wait_p95_ms === null ? '—' : `${(day.queue_wait_p95_ms / 1000).toFixed(1)} s`}
      </Box>
    </Box>
  );
}
