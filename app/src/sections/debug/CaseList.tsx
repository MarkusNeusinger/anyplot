/**
 * The rows of the agent cases list: a grid per case on `sm` and up (reaction
 * and age, the case line with its message and markers, the tags, the status and
 * `.open()`), the same content stacked at phone width. A row is tinted while
 * its status is `new`, like the feedback list above it.
 */

import Box from '@mui/material/Box';

import { type AgentCase, CASE_STATUSES, type CaseStatus, caseVersionLabel } from 'src/lib/agent';
import { REACTION_TEXT, reactionOption } from 'src/sections/agent-chat/reactions';
import { ghostButtonSx, visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import { acceptMatch } from 'src/sections/debug/acceptMatch';
import { formatUtc, timeAgo } from 'src/sections/debug/format';
import { chipSx, debugControlSx, listMutedSx, listTextSx } from 'src/sections/debug/styles';
import { TagChips } from 'src/sections/debug/TagsEditor';
import { colors, fontSize, semanticColors } from 'src/theme';

export interface CaseListProps {
  items: AgentCase[];
  selectedId: string | null;
  /** Ids with a change in flight. */
  busy: Record<string, boolean>;
  /** The failure line of a case's last change, by id. */
  errors: Record<string, string>;
  onOpen: (id: string) => void;
  onClose: () => void;
  onStatus: (id: string, status: CaseStatus) => void;
}

/** The case's markers: what the triage should notice before opening it. */
export function CaseMarkers({ item }: { item: AgentCase }) {
  const contradicts = acceptMatch(item.reaction, item.pipeline_status) === false;
  if (!item.promoted_at && !item.superseded_by && !contradicts && item.include_data) return null;
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
      {item.promoted_at && (
        <Box component="span" sx={{ ...chipSx, borderColor: colors.primary }}>
          promoted
        </Box>
      )}
      {item.superseded_by && (
        <Box component="span" sx={chipSx}>
          superseded
        </Box>
      )}
      {contradicts && (
        <Box component="span" sx={{ ...chipSx, borderColor: colors.warning }}>
          <Box
            component="span"
            aria-hidden
            sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: colors.warning }}
          />
          contradicts pipeline
        </Box>
      )}
      {!item.include_data && (
        <Box component="span" sx={chipSx}>
          no data
        </Box>
      )}
    </Box>
  );
}

/** The reaction as its filled icon in its colour; the words for screen readers. */
export function ReactionMark({ reaction }: { reaction: string }) {
  const entry = reactionOption(reaction);
  const text = entry ? REACTION_TEXT[entry.value] : reaction;
  return (
    <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center' }}>
      {entry && (
        <Box
          component="span"
          aria-hidden
          sx={{ display: 'inline-flex', color: entry.color, fontSize: 18 }}
        >
          <entry.Filled fontSize="inherit" />
        </Box>
      )}
      <Box component="span" sx={entry ? visuallyHiddenSx : listTextSx}>
        {text}
      </Box>
    </Box>
  );
}

export function CaseList({
  items,
  selectedId,
  busy,
  errors,
  onOpen,
  onClose,
  onStatus,
}: CaseListProps) {
  return (
    <Box
      component="ul"
      aria-label="Agent cases"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1, m: 0, p: 0, listStyle: 'none' }}
    >
      {items.map(item => {
        const selected = item.id === selectedId;
        const error = errors[item.id];
        return (
          <Box
            component="li"
            key={item.id}
            data-case-id={item.id}
            sx={{
              border: '1px solid',
              borderColor: selected ? colors.primary : 'var(--rule)',
              borderRadius: 1,
              p: 1.5,
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'auto minmax(0, 1fr) auto auto' },
              columnGap: 1.5,
              rowGap: 0.75,
              alignItems: 'start',
              bgcolor: item.status === 'new' ? 'var(--bg-surface)' : 'transparent',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, minWidth: 90 }}>
              <ReactionMark reaction={item.reaction} />
              <Box
                component="time"
                dateTime={item.created_at}
                title={formatUtc(item.created_at)}
                sx={{ ...listMutedSx, fontSize: fontSize.xxs }}
              >
                {timeAgo(item.created_at)}
              </Box>
            </Box>
            <Box sx={{ minWidth: 0 }}>
              <Box sx={{ ...listTextSx, fontWeight: 600, overflowWrap: 'anywhere' }}>
                {item.spec_id ?? '—'} · {item.library_id ?? '—'} ·{' '}
                {caseVersionLabel(item.result_version)}
              </Box>
              <Box
                sx={{
                  ...listTextSx,
                  color: item.message ? 'var(--ink)' : semanticColors.mutedText,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {item.message ?? 'no message'}
              </Box>
              <CaseMarkers item={item} />
            </Box>
            {/* Always a cell, so the controls stay in the last column of every row. */}
            <Box
              sx={{
                minWidth: 0,
                display: item.tags.length ? 'block' : { xs: 'none', sm: 'block' },
              }}
            >
              <TagChips tags={item.tags} />
            </Box>
            <Box sx={{ display: 'flex', gap: 0.75, alignItems: 'center', flexWrap: 'wrap' }}>
              <Box
                component="select"
                aria-label={`Status of case ${item.id}`}
                value={item.status}
                disabled={!!busy[item.id]}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                  onStatus(item.id, event.target.value as CaseStatus)
                }
                // One width for every status, so `.open()` lines up from row to row.
                sx={{ ...debugControlSx, cursor: 'pointer', width: 124 }}
              >
                {CASE_STATUSES.map(status => (
                  <option key={status} value={status}>
                    {status.replace('_', ' ')}
                  </option>
                ))}
              </Box>
              <Box
                component="button"
                type="button"
                aria-label={`${selected ? 'Close' : 'Open'} case ${item.id}`}
                aria-expanded={selected}
                onClick={() => (selected ? onClose() : onOpen(item.id))}
                sx={{ ...ghostButtonSx, minWidth: '9ch' }}
              >
                {selected ? '.close()' : '.open()'}
              </Box>
            </Box>
            {error && (
              <Box
                role="alert"
                sx={{
                  ...listTextSx,
                  color: colors.error,
                  gridColumn: '1 / -1',
                  overflowWrap: 'anywhere',
                }}
              >
                {error}
              </Box>
            )}
          </Box>
        );
      })}
    </Box>
  );
}
