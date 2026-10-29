import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { timeAgo } from 'src/sections/debug/format';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface FeedbackTopPage {
  path: string;
  count: number;
  last_seen: string | null;
}

export function FeedbackTopList({
  title,
  items,
  accent,
}: {
  title: string;
  items: FeedbackTopPage[];
  accent: string;
}) {
  return (
    <Box sx={{ border: '1px solid var(--rule)', borderRadius: 1, p: 1.5 }}>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          fontWeight: 600,
          color: 'var(--ink-soft)',
          mb: 1,
        }}
      >
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
          no entries yet
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
          {items.map(it => (
            <Box
              key={it.path}
              sx={{
                display: 'grid',
                gridTemplateColumns: '32px 1fr auto',
                gap: 1,
                alignItems: 'baseline',
                py: 0.4,
                borderBottom: '1px solid var(--rule)',
                '&:last-of-type': { borderBottom: 'none' },
              }}
            >
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  color: accent,
                  fontWeight: 600,
                  textAlign: 'right',
                }}
              >
                {it.count}
              </Typography>
              <Link
                component={RouterLink}
                to={it.path}
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xs,
                  color: colors.primary,
                  textDecoration: 'none',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                {it.path}
              </Link>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.micro,
                  color: semanticColors.mutedText,
                }}
              >
                {it.last_seen ? timeAgo(it.last_seen) : ''}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
