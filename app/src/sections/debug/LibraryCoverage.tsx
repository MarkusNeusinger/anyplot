import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { scoreColor } from 'src/sections/debug/debugFormat';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface LibraryStats {
  id: string;
  name: string;
  impl_count: number;
  avg_score: number | null;
  min_score: number | null;
  max_score: number | null;
}

export function LibraryCoverage({ stats }: { stats: LibraryStats[] }) {
  const maxLibCount = Math.max(...stats.map(lib => lib.impl_count), 1);

  return (
    <>
      {/* Library Coverage */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>libraries</em>} />
      </Box>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 1,
        }}
      >
        impl count · avg · min–max
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {[...stats]
          .sort((a, b) => b.impl_count - a.impl_count)
          .map(lib => (
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
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xs,
                  color: semanticColors.mutedText,
                  textAlign: 'right',
                }}
              >
                {lib.name}
              </Typography>
              <Box
                sx={{
                  height: 10,
                  bgcolor: 'var(--bg-elevated)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}
              >
                <Box
                  sx={{
                    width: `${(lib.impl_count / maxLibCount) * 100}%`,
                    height: '100%',
                    bgcolor: colors.primaryDark,
                    opacity: 0.5,
                  }}
                />
              </Box>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  color: 'var(--ink-soft)',
                  fontWeight: 600,
                  textAlign: 'right',
                }}
              >
                {lib.impl_count}
              </Typography>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  color: scoreColor(lib.avg_score),
                  fontWeight: 600,
                  textAlign: 'right',
                }}
              >
                {lib.avg_score ?? '—'}
              </Typography>
              <Typography
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.xxs,
                  color: semanticColors.mutedText,
                  textAlign: 'right',
                }}
              >
                {lib.min_score?.toFixed(0) ?? '—'}–{lib.max_score?.toFixed(0) ?? '—'}
              </Typography>
            </Box>
          ))}
      </Box>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: '80px 1fr 40px 40px 70px',
          gap: 1.5,
          mt: 0.5,
          fontFamily: typography.fontFamily,
          fontSize: fontSize.micro,
          color: semanticColors.mutedText,
        }}
      >
        <span />
        <span />
        <Box component="span" sx={{ textAlign: 'right' }}>
          count
        </Box>
        <Box component="span" sx={{ textAlign: 'right' }}>
          avg
        </Box>
        <Box component="span" sx={{ textAlign: 'right' }}>
          min–max
        </Box>
      </Box>
    </>
  );
}
