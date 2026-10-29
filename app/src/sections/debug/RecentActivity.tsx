import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { specPath } from 'src/routes/paths';
import { scoreColor } from 'src/sections/debug/debugFormat';
import { timeAgo } from 'src/sections/debug/format';
import { fontSize, semanticColors, typography } from 'src/theme';

export interface RecentActivityData {
  spec_id: string;
  spec_title: string;
  library_id: string;
  language_id: string;
  quality_score: number | null;
  generated_by: string | null;
  updated: string;
}

export function RecentActivity({ activity }: { activity: RecentActivityData[] }) {
  if (activity.length === 0) return null;
  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>recent activity</em>} />
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {activity.map((act, idx) => (
          <Link
            key={`${act.spec_id}-${act.library_id}-${idx}`}
            component={RouterLink}
            to={specPath(act.spec_id, act.language_id, act.library_id)}
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '55px 1fr 30px',
                sm: '65px 90px minmax(0, 1fr) 30px 130px',
              },
              gap: { xs: 1, sm: 1.5 },
              alignItems: 'center',
              textDecoration: 'none',
              color: 'inherit',
              py: 0.5,
              borderBottom: '1px solid var(--rule)',
              '&:hover': { bgcolor: 'var(--bg-surface)' },
            }}
          >
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xs,
                color: semanticColors.mutedText,
              }}
            >
              {timeAgo(act.updated)}
            </Typography>
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xs,
                color: 'var(--ink-soft)',
                display: { xs: 'none', sm: 'block' },
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {act.library_id}
            </Typography>
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xs,
                color: 'var(--ink)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                minWidth: 0,
              }}
            >
              <Box
                component="span"
                sx={{
                  display: { xs: 'inline', sm: 'none' },
                  color: semanticColors.mutedText,
                  mr: 0.5,
                }}
              >
                {act.library_id} ·
              </Box>
              {act.spec_title}
            </Typography>
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xs,
                color: scoreColor(act.quality_score),
                fontWeight: 600,
                textAlign: 'right',
              }}
            >
              {act.quality_score !== null ? Math.round(act.quality_score) : '—'}
            </Typography>
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.xxs,
                color: semanticColors.mutedText,
                display: { xs: 'none', sm: 'block' },
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                textAlign: 'right',
              }}
            >
              {act.generated_by ?? '—'}
            </Typography>
          </Link>
        ))}
      </Box>
    </>
  );
}
