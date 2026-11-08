import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { timeAgo } from 'src/sections/debug/format';
import { listMutedSx, listTextSx } from 'src/sections/debug/styles';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

/** One plot's votes from `GET /debug/feedback/votes`: counts only, never a session or a message. */
export interface FeedbackVoteItem {
  spec_id: string;
  language: string | null;
  library_id: string;
  path: string;
  /** The current version's votes (`core/plot_votes.py`). */
  thumbs_up: number;
  thumbs_down: number;
  /** The votes cast on the versions before the plot's last regeneration. */
  earlier_thumbs_up: number;
  earlier_thumbs_down: number;
  last_vote: string | null;
}

/** How the list ranks the plots: the API's `sort`, by the current version's counts. */
export type VoteSort = 'thumbs_down' | 'thumbs_up' | 'total';

const HEADERS: Record<VoteSort, { label: string; title: string }> = {
  thumbs_up: { label: '👍', title: 'thumbs up on the current version' },
  thumbs_down: { label: '👎', title: 'thumbs down on the current version' },
  total: { label: 'total', title: 'all thumbs on the current version' },
};

// plot · 👍 · 👎 · total · earlier · last vote (the last column only from md up)
const GRID = {
  display: 'grid',
  gridTemplateColumns: {
    xs: 'minmax(0, 1fr) 28px 28px 40px 56px',
    md: 'minmax(0, 1fr) 36px 36px 48px 72px 80px',
  },
  columnGap: 1,
  alignItems: 'baseline',
} as const;

const numberSx = { ...listTextSx, textAlign: 'right', fontVariantNumeric: 'tabular-nums' } as const;

/**
 * The plots with the most votes, one row per implementation: the current
 * version's 👍 and 👎 and their total, the earlier versions' counts beside
 * them, and the newest vote. The 👍, 👎 and total headers sort the list.
 */
export function FeedbackTopList({
  items,
  sort,
  onSortChange,
}: {
  items: FeedbackVoteItem[];
  sort: VoteSort;
  onSortChange: (sort: VoteSort) => void;
}) {
  const header = (key: VoteSort) => {
    const active = key === sort;
    return (
      <Box
        component="button"
        type="button"
        key={key}
        title={`sort by ${HEADERS[key].title}`}
        aria-label={`sort by ${HEADERS[key].title}`}
        aria-pressed={active}
        onClick={() => onSortChange(key)}
        sx={{
          ...listTextSx,
          textAlign: 'right',
          p: 0,
          // WCAG 2.5.8: a 24 px target even in the phone's 28 px column
          minHeight: 24,
          minWidth: 24,
          border: 'none',
          bgcolor: 'transparent',
          cursor: 'pointer',
          fontWeight: active ? 700 : 400,
          color: active ? 'var(--ink)' : semanticColors.mutedText,
          textDecoration: active ? 'underline' : 'none',
          textUnderlineOffset: '3px',
          '&:hover': { color: 'var(--ink)' },
          '&:focus-visible': { outline: `1px solid ${colors.primary}`, outlineOffset: '2px' },
        }}
      >
        {HEADERS[key].label}
      </Box>
    );
  };

  return (
    <Box sx={{ border: '1px solid var(--rule)', borderRadius: 1, p: 1.5 }}>
      <Box sx={{ ...GRID, pb: 0.75, mb: 0.25, borderBottom: '1px solid var(--rule)' }}>
        <Typography component="span" sx={listMutedSx}>
          plot
        </Typography>
        {header('thumbs_up')}
        {header('thumbs_down')}
        {header('total')}
        <Typography
          component="span"
          title="thumbs up · down on the versions before the last regeneration"
          sx={{ ...listMutedSx, textAlign: 'right' }}
        >
          earlier
        </Typography>
        <Typography
          component="span"
          sx={{
            ...listMutedSx,
            textAlign: 'right',
            whiteSpace: 'nowrap',
            display: { xs: 'none', md: 'block' },
          }}
        >
          last vote
        </Typography>
      </Box>
      {items.length === 0 ? (
        <Typography sx={{ ...listMutedSx, pt: 0.75 }}>no votes yet</Typography>
      ) : (
        items.map(it => {
          const earlier = it.earlier_thumbs_up + it.earlier_thumbs_down;
          return (
            <Box
              key={it.path}
              data-testid="vote-row"
              sx={{
                ...GRID,
                py: 0.5,
                borderBottom: '1px solid var(--rule)',
                '&:last-of-type': { borderBottom: 'none' },
              }}
            >
              <Link
                component={RouterLink}
                to={it.path}
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xs,
                  color: colors.primary,
                  textDecoration: 'none',
                  // On a phone the path wraps, so the library at its end stays readable.
                  overflow: 'hidden',
                  overflowWrap: 'anywhere',
                  textOverflow: { md: 'ellipsis' },
                  whiteSpace: { xs: 'normal', md: 'nowrap' },
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {it.path}
              </Link>
              <Typography
                component="span"
                sx={{
                  ...numberSx,
                  color: it.thumbs_up ? colors.success : semanticColors.mutedText,
                }}
              >
                {it.thumbs_up}
              </Typography>
              <Typography
                component="span"
                sx={{
                  ...numberSx,
                  color: it.thumbs_down ? colors.error : semanticColors.mutedText,
                }}
              >
                {it.thumbs_down}
              </Typography>
              <Typography component="span" sx={{ ...numberSx, fontWeight: 600 }}>
                {it.thumbs_up + it.thumbs_down}
              </Typography>
              <Typography
                component="span"
                title={
                  earlier
                    ? `${it.earlier_thumbs_up} up, ${it.earlier_thumbs_down} down on earlier versions`
                    : 'no votes on earlier versions'
                }
                sx={{ ...listMutedSx, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}
              >
                {earlier ? `${it.earlier_thumbs_up} · ${it.earlier_thumbs_down}` : '–'}
              </Typography>
              <Typography
                component="span"
                sx={{
                  ...listMutedSx,
                  fontSize: fontSize.xxs,
                  textAlign: 'right',
                  display: { xs: 'none', md: 'block' },
                }}
              >
                {it.last_vote ? timeAgo(it.last_vote) : ''}
              </Typography>
            </Box>
          );
        })
      )}
    </Box>
  );
}
