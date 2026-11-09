/**
 * The debug page's "machine readers" section: every machine read of the last 7
 * or 30 UTC days from the content-free machine-read telemetry
 * (`GET /debug/machine-readers`, `api/machine_reads_query.py`).
 *
 * - Four tiles: live requests, the verified share (with its counts), MCP
 *   requests and the named vendors.
 * - One matrix, a row per vendor and purpose, most requests first: Cloudflare's
 *   category on most of its verified lines, the verified and unverified counts,
 *   the surfaces, the 404s and the most requested route. A row opens to its
 *   five most requested routes.
 * - One row per UTC day, newest first: the verified lines by audience, the
 *   unverified apart, and the MCP requests.
 * - Unlike the public tile, every status, surface and verdict counts here;
 *   lines of the smoke checks (`synthetic`) are only counted in the meta line.
 * - BigQuery not set up yet, a failed query, a failed request, an unreadable
 *   answer and a window without lines are one muted line each.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DEBUG_API_URL } from 'src/constants';
import { UsageTile } from 'src/sections/debug/AgentUsageSection';
import { timeAgo } from 'src/sections/debug/format';
import {
  debugControlSx,
  listMutedSx,
  listTextSx,
  tableCellSx,
  tableHeadSx,
} from 'src/sections/debug/styles';
import { useAnswer } from 'src/sections/debug/useAnswer';
import { colors } from 'src/theme';

/** The windows the endpoint takes, in days. */
const WINDOWS = [7, 30] as const;
type MachineReadsWindow = (typeof WINDOWS)[number];

export interface MachineReadsPath {
  key: string;
  count: number;
}

export interface MachineReadsVendor {
  assistant: string;
  kind: string;
  /** Cloudflare's category on most of the row's verified lines; `null` when none was verified. */
  category: string | null;
  requests: number;
  verified: number;
  unverified: number;
  pages: number;
  code: number;
  og: number;
  mcp: number;
  not_found: number;
  top_paths: MachineReadsPath[];
}

export interface MachineReadsDay {
  date: string;
  for_person: number;
  index_training: number;
  search: number;
  seo: number;
  other: number;
  unverified: number;
  mcp: number;
}

/** The answer of `GET /debug/machine-readers?days=N`. */
export interface MachineReadsDetail {
  status: 'ok' | 'not_configured' | 'unavailable';
  days: number;
  generated_at: string | null;
  requests: number;
  verified: number;
  unverified: number;
  mcp_calls: number;
  synthetic: number;
  vendors: MachineReadsVendor[];
  daily: MachineReadsDay[];
}

const STATUSES = new Set<string>(['ok', 'not_configured', 'unavailable']);
const MAX_PATHS = 5;

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object';

function readPaths(value: unknown): MachineReadsPath[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(
      (item): item is Record<string, unknown> =>
        isRecord(item) && typeof item.key === 'string' && item.key !== ''
    )
    .slice(0, MAX_PATHS)
    .map(item => ({ key: item.key as string, count: count(item.count) }));
}

function readVendor(row: unknown): MachineReadsVendor | null {
  if (!isRecord(row) || typeof row.assistant !== 'string' || typeof row.kind !== 'string') {
    return null;
  }
  return {
    assistant: row.assistant,
    kind: row.kind,
    category: typeof row.category === 'string' && row.category ? row.category : null,
    requests: count(row.requests),
    verified: count(row.verified),
    unverified: count(row.unverified),
    pages: count(row.pages),
    code: count(row.code),
    og: count(row.og),
    mcp: count(row.mcp),
    not_found: count(row.not_found),
    top_paths: readPaths(row.top_paths),
  };
}

/** The answer as the section reads it; `null` for one without a known status. */
function readMachineReads(body: unknown): MachineReadsDetail | null {
  if (!isRecord(body) || typeof body.status !== 'string' || !STATUSES.has(body.status)) {
    return null;
  }
  const vendors = (Array.isArray(body.vendors) ? body.vendors : [])
    .map(readVendor)
    .filter((vendor): vendor is MachineReadsVendor => vendor !== null)
    .sort((a, b) => b.requests - a.requests);
  const daily = (Array.isArray(body.daily) ? body.daily : [])
    .filter((day): day is Record<string, unknown> => isRecord(day) && typeof day.date === 'string')
    .map(day => ({
      date: day.date as string,
      for_person: count(day.for_person),
      index_training: count(day.index_training),
      search: count(day.search),
      seo: count(day.seo),
      other: count(day.other),
      unverified: count(day.unverified),
      mcp: count(day.mcp),
    }));
  return {
    status: body.status as MachineReadsDetail['status'],
    days: count(body.days),
    generated_at: typeof body.generated_at === 'string' ? body.generated_at : null,
    requests: count(body.requests),
    verified: count(body.verified),
    unverified: count(body.unverified),
    mcp_calls: count(body.mcp_calls),
    synthetic: count(body.synthetic),
    vendors,
    daily,
  };
}

const EMPTY_TEXT: Record<'not_configured' | 'unavailable' | 'empty', string> = {
  not_configured: 'machine-read telemetry is not configured yet',
  unavailable: 'crawler numbers unavailable right now',
  empty: 'no machine reads in this window',
};

const number = (value: number): string => value.toLocaleString('en-US');

const subheadSx = {
  ...listTextSx,
  fontWeight: 600,
  color: 'var(--ink-soft)',
  mt: 3,
  mb: 0.75,
} as const;

export interface MachineReadersSectionProps {
  /** The admin token of the page (`X-Admin-Token`), or `''` behind Cloudflare Access. */
  token: string;
  /** The page's reload count: a change fetches the numbers again. */
  reloadCounter: number;
}

export function MachineReadersSection({ token, reloadCounter }: MachineReadersSectionProps) {
  const [days, setDays] = useState<MachineReadsWindow>(7);
  const detail = useAnswer(
    `${DEBUG_API_URL}/debug/machine-readers?days=${days}`,
    token,
    reloadCounter,
    readMachineReads
  );
  const empty: keyof typeof EMPTY_TEXT | null =
    detail === undefined
      ? null
      : !detail || detail.status === 'unavailable'
        ? 'unavailable'
        : detail.status === 'not_configured'
          ? 'not_configured'
          : detail.requests === 0
            ? 'empty'
            : null;
  const vendorCount = detail
    ? new Set(detail.vendors.map(vendor => vendor.assistant).filter(name => name !== 'other')).size
    : 0;

  return (
    <Box component="section" aria-label="Machine readers section" sx={{ mb: 4 }}>
      <Box sx={{ mt: 4, display: 'flex', alignItems: 'center', columnGap: 2, flexWrap: 'wrap' }}>
        <SectionHeader prompt="❯" title={<em>machine readers</em>} />
        <Box
          role="group"
          aria-label="Machine readers window"
          sx={{ ml: 'auto', mb: { xs: 2, sm: 0 }, display: 'flex', gap: 0.5 }}
        >
          {WINDOWS.map(span => {
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
        content-free request lines · last {days} days
        {detail?.generated_at ? ` · generated ${timeAgo(detail.generated_at)}` : ''}
        {detail && detail.synthetic > 0
          ? ` · ${number(detail.synthetic)} synthetic lines (smoke checks) left out`
          : ''}
      </Typography>

      {detail === undefined ? (
        <Typography sx={{ ...listMutedSx, py: 1 }}>loading machine reads…</Typography>
      ) : empty || !detail ? (
        <Typography data-testid="machine-readers-empty" sx={{ ...listMutedSx, py: 1 }}>
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
            <UsageTile label="requests" value={number(detail.requests)} />
            <UsageTile
              label="verified"
              value={`${Math.round((detail.verified / detail.requests) * 100)}%`}
              detail={`${number(detail.verified)} of ${number(detail.requests)}`}
            />
            <UsageTile label="mcp calls" value={number(detail.mcp_calls)} />
            <UsageTile label="vendors" value={number(vendorCount)} />
          </Box>
          <VendorMatrix vendors={detail.vendors} />
          <DailyTable days={detail.daily} />
        </>
      )}
    </Box>
  );
}

const MATRIX_COLUMNS = [
  'vendor',
  'kind',
  'category',
  'requests',
  'verified',
  'unverified',
  'pages',
  'code',
  'og',
  'mcp',
  '404',
  'top path',
] as const;
/** The text columns; the rest are counts, right-aligned. */
const TEXT_COLUMNS = new Set<string>(['vendor', 'kind', 'category', 'top path']);

function VendorMatrix({ vendors }: { vendors: MachineReadsVendor[] }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <Box role="group" aria-label="Machine readers by vendor">
      <Typography sx={subheadSx}>
        by vendor and purpose · every status and surface · open a row for its top routes
      </Typography>
      <Box sx={{ overflowX: 'auto' }}>
        <Box component="table" sx={{ borderCollapse: 'collapse', minWidth: 880, width: '100%' }}>
          <Box component="thead">
            <Box component="tr">
              {MATRIX_COLUMNS.map(column => (
                <Box
                  component="th"
                  key={column}
                  scope="col"
                  sx={{ ...tableHeadSx, textAlign: TEXT_COLUMNS.has(column) ? 'left' : 'right' }}
                >
                  {column}
                </Box>
              ))}
            </Box>
          </Box>
          <Box component="tbody">
            {vendors.map(vendor => {
              const id = `${vendor.assistant}/${vendor.kind}`;
              return (
                <VendorRow
                  key={id}
                  vendor={vendor}
                  open={open === id}
                  onToggle={() => setOpen(open === id ? null : id)}
                />
              );
            })}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

function VendorRow({
  vendor,
  open,
  onToggle,
}: {
  vendor: MachineReadsVendor;
  open: boolean;
  onToggle: () => void;
}) {
  const muted = { ...tableCellSx, color: 'var(--ink-muted)' };
  const counts = [
    vendor.requests,
    vendor.verified,
    vendor.unverified,
    vendor.pages,
    vendor.code,
    vendor.og,
    vendor.mcp,
    vendor.not_found,
  ];
  const top = vendor.top_paths[0];
  return (
    <>
      <Box component="tr">
        <Box component="th" scope="row" sx={{ ...tableCellSx, textAlign: 'left', fontWeight: 400 }}>
          <Box
            component="button"
            type="button"
            aria-expanded={open}
            aria-label={`${vendor.assistant} ${vendor.kind}: top routes`}
            onClick={onToggle}
            disabled={vendor.top_paths.length === 0}
            sx={{
              ...listTextSx,
              p: 0,
              border: 'none',
              bgcolor: 'transparent',
              cursor: vendor.top_paths.length ? 'pointer' : 'default',
              '&:focus-visible': { outline: `1px solid ${colors.primary}` },
            }}
          >
            {open ? '▾' : '▸'} {vendor.assistant}
          </Box>
        </Box>
        <Box component="td" sx={{ ...tableCellSx, textAlign: 'left', color: 'var(--ink-soft)' }}>
          {vendor.kind}
        </Box>
        <Box component="td" sx={{ ...tableCellSx, textAlign: 'left', color: 'var(--ink-soft)' }}>
          {vendor.category ?? 'unverified'}
        </Box>
        {counts.map((value, index) => (
          <Box
            component="td"
            key={MATRIX_COLUMNS[index + 3]}
            sx={value === 0 ? muted : tableCellSx}
          >
            {number(value)}
          </Box>
        ))}
        <Box
          component="td"
          title={top?.key}
          sx={{
            ...tableCellSx,
            textAlign: 'left',
            maxWidth: 220,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {top ? top.key : '—'}
        </Box>
      </Box>
      {open && (
        <Box component="tr">
          <Box
            component="td"
            colSpan={MATRIX_COLUMNS.length}
            sx={{ ...tableCellSx, textAlign: 'left' }}
          >
            <Box
              component="ol"
              aria-label={`${vendor.assistant} ${vendor.kind} top routes`}
              sx={{ m: 0, pl: 2.5, py: 0.25, listStyle: 'none' }}
            >
              {vendor.top_paths.map(path => (
                <Box component="li" key={path.key} sx={{ ...listTextSx, py: 0.15 }}>
                  {number(path.count)} · {path.key}
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      )}
    </>
  );
}

const DAY_COLUMNS = [
  'day (UTC)',
  'for a person',
  'index & training',
  'search',
  'seo',
  'other',
  'unverified',
  'mcp',
] as const;

function DailyTable({ days }: { days: MachineReadsDay[] }) {
  return (
    <Box role="group" aria-label="Machine reads per day">
      <Typography sx={subheadSx}>per day · verified lines by audience, newest first</Typography>
      <Box sx={{ overflowX: 'auto' }}>
        <Box component="table" sx={{ borderCollapse: 'collapse', minWidth: 560, width: '100%' }}>
          <Box component="thead">
            <Box component="tr">
              {DAY_COLUMNS.map((column, index) => (
                <Box
                  component="th"
                  key={column}
                  scope="col"
                  sx={{ ...tableHeadSx, textAlign: index === 0 ? 'left' : 'right' }}
                >
                  {column}
                </Box>
              ))}
            </Box>
          </Box>
          <Box component="tbody">
            {days.map((day, index) => (
              <Box component="tr" key={day.date}>
                <Box
                  component="th"
                  scope="row"
                  sx={{ ...tableCellSx, textAlign: 'left', fontWeight: 400 }}
                >
                  {day.date}
                  {index === 0 ? ' · so far' : ''}
                </Box>
                {[
                  day.for_person,
                  day.index_training,
                  day.search,
                  day.seo,
                  day.other,
                  day.unverified,
                  day.mcp,
                ].map((value, column) => (
                  <Box component="td" key={DAY_COLUMNS[column + 1]} sx={tableCellSx}>
                    {number(value)}
                  </Box>
                ))}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
      <Typography sx={{ ...listMutedSx, mt: 0.75 }}>
        the audiences count verified lines only · other: link previews and every other category ·
        unverified: every line without cloudflare&apos;s verdict, whatever its name
      </Typography>
    </Box>
  );
}
