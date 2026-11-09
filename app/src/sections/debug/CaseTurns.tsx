/**
 * The case detail's turn record as one compact matrix: a row per turn with
 * the page's action or a message, how the turn ended, and as chips the guards
 * that fired and the tool calls; the worst entry marks the row. A click opens
 * the turn's whole record below its row. Closed codes only, never a word of
 * the user: the transcript below labels its lines with the same turn numbers.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import type { AgentCaseTurn, AgentCaseTurns } from 'src/lib/agent';
import { smallText } from 'src/sections/agent-chat/styles';
import {
  actionLabel,
  callLabel,
  endLine,
  type Severity,
  sharedTurns,
  type TurnChip,
  turnChips,
  turnSeverity,
  turnsSummary,
} from 'src/sections/debug/caseTurns';
import { chipSx, detailMutedSx, detailTextSx } from 'src/sections/debug/styles';
import { colors, typography } from 'src/theme';

const MARK: Record<Severity, string> = {
  ok: 'var(--rule)',
  warn: colors.warning,
  bad: colors.error,
};

/** Turn, action, end, chips: the header and every row share the columns from 600 px up. */
const columnsSx = {
  display: 'grid',
  gridTemplateColumns: { xs: 'auto auto minmax(0, 1fr)', sm: '3em 9.5em 5.5em minmax(0, 1fr)' },
  columnGap: 1.5,
  rowGap: 0.5,
  alignItems: 'baseline',
} as const;

const monoSx = { fontFamily: typography.mono, fontSize: smallText } as const;

function Chip({ chip }: { chip: TurnChip }) {
  return (
    <Box
      component="span"
      sx={{
        ...chipSx,
        ...monoSx,
        whiteSpace: 'normal',
        overflowWrap: 'anywhere',
        color: chip.severity === 'ok' ? 'var(--ink-soft)' : 'var(--ink)',
        borderColor: MARK[chip.severity],
        borderLeftWidth: chip.severity === 'ok' ? 1 : 3,
      }}
    >
      {chip.count > 1 ? `${chip.label} ×${chip.count}` : chip.label}
    </Box>
  );
}

/** A list of the record's entries, and what its bound left out (`note` as singular and plural). */
function Entries({
  items,
  dropped,
  note,
}: {
  items: string[];
  dropped: number;
  note: [string, string];
}) {
  if (items.length === 0 && dropped === 0) return <Box sx={detailMutedSx}>none</Box>;
  return (
    <>
      <Box component="ol" sx={{ m: 0, pl: 2.5, overflowWrap: 'anywhere' }}>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </Box>
      {dropped > 0 && (
        <Box sx={detailMutedSx}>{`${dropped} ${note[dropped === 1 ? 0 : 1]} not recorded`}</Box>
      )}
    </>
  );
}

function TurnDetails({
  id,
  record,
  shared,
}: {
  id: string;
  record: AgentCaseTurn;
  shared: boolean;
}) {
  return (
    <Box
      id={id}
      component="dl"
      sx={{
        ...detailTextSx,
        ...monoSx,
        m: 0,
        px: 1.5,
        pb: 1.25,
        display: 'grid',
        gridTemplateColumns: 'max-content minmax(0, 1fr)',
        columnGap: 2,
        rowGap: 0.75,
        '& dt': { color: 'var(--ink-muted)' },
        '& dd': { m: 0, minWidth: 0 },
      }}
    >
      <dt>ended</dt>
      <dd>{endLine(record)}</dd>
      <dt>calls</dt>
      <dd>
        <Entries
          items={record.tools.map(
            // A refused call can still have kept its request (`data_changed_this_turn`).
            call =>
              `${callLabel(call)}${call.verdict === 'allowed' || call.outcome === 'refused' ? '' : ` (${call.outcome})`}`
          )}
          dropped={record.tools_dropped}
          note={['later call', 'later calls']}
        />
      </dd>
      <dt>guards</dt>
      <dd>
        <Entries
          items={record.guards.map(line => `${line.guard}: ${line.verdict}`)}
          dropped={record.guards_dropped}
          note={['earlier verdict', 'earlier verdicts']}
        />
      </dd>
      <dt>prep ops</dt>
      <dd>
        <Entries
          items={record.prep_ops}
          dropped={record.prep_ops_dropped}
          note={['later operation', 'later operations']}
        />
      </dd>
      {shared && (
        <>
          <dt>note</dt>
          <dd>
            {`two records share turn ${record.turn}: a turn refused before the scope judge keeps no transcript line and takes the next turn's number`}
          </dd>
        </>
      )}
    </Box>
  );
}

export function CaseTurns({ turns }: { turns: AgentCaseTurns | null | undefined }) {
  const [open, setOpen] = useState<ReadonlySet<number>>(() => new Set());
  if (!turns) {
    return (
      <Box sx={detailMutedSx}>
        no turn record: this case was sent before feedback cases kept one
      </Box>
    );
  }
  if (turns.records.length === 0) {
    return (
      <Box sx={detailMutedSx}>
        {turns.dropped > 0
          ? `the record kept none of the session's ${turns.dropped} turns`
          : 'no turn recorded: the session ran no turn before the feedback'}
      </Box>
    );
  }
  const shared = sharedTurns(turns);
  const toggle = (index: number) =>
    setOpen(previous => {
      const next = new Set(previous);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, minWidth: 0 }}>
      <Box sx={detailMutedSx}>{turnsSummary(turns)}</Box>
      <Box
        aria-hidden
        sx={{
          ...columnsSx,
          ...detailMutedSx,
          display: { xs: 'none', sm: 'grid' },
          pl: 1.5,
          borderLeft: '3px solid transparent',
        }}
      >
        <span>turn</span>
        <span>action</span>
        <span>ended</span>
        <span>guards that fired · tool calls</span>
      </Box>
      <Box
        component="ol"
        aria-label="Turns"
        sx={{ m: 0, p: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 0.5 }}
      >
        {turns.records.map((record, index) => {
          const severity = turnSeverity(record);
          const chips = turnChips(record);
          const id = `case-turn-${index}`;
          const expanded = open.has(index);
          return (
            <Box
              component="li"
              key={index}
              sx={{
                borderLeft: `3px solid ${MARK[severity]}`,
                bgcolor: expanded ? 'var(--bg-surface)' : 'transparent',
                borderRadius: '0 4px 4px 0',
                minWidth: 0,
              }}
            >
              <Box
                component="button"
                type="button"
                aria-expanded={expanded}
                aria-controls={expanded ? id : undefined}
                onClick={() => toggle(index)}
                sx={{
                  ...columnsSx,
                  ...detailTextSx,
                  width: '100%',
                  textAlign: 'left',
                  bgcolor: 'transparent',
                  border: 'none',
                  px: 1.5,
                  py: 0.75,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'var(--bg-surface)' },
                  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: -2 },
                }}
              >
                <Box component="span" sx={{ ...monoSx, fontWeight: 600 }}>
                  {`#${record.turn}`}
                </Box>
                <Box component="span" sx={{ ...monoSx, overflowWrap: 'anywhere' }}>
                  {actionLabel(record.action)}
                </Box>
                <Box component="span" sx={monoSx}>
                  {record.kind}
                </Box>
                <Box
                  component="span"
                  sx={{
                    gridColumn: { xs: '1 / -1', sm: 'auto' },
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 0.5,
                  }}
                >
                  {chips.length > 0 ? (
                    chips.map((chip, at) => <Chip key={at} chip={chip} />)
                  ) : (
                    <Box component="span" sx={detailMutedSx}>
                      no tool call, no guard fired
                    </Box>
                  )}
                </Box>
              </Box>
              {expanded && <TurnDetails id={id} record={record} shared={shared.has(record.turn)} />}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
