import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface DailyImplPoint {
  date: string;
  impls_updated: number;
}

export function DailyActivityChart({ data }: { data: DailyImplPoint[] }) {
  const maxDaily = Math.max(...data.map(p => p.impls_updated), 1);
  const firstDate = data[0]?.date ?? '';
  const lastDate = data[data.length - 1]?.date ?? '';

  return (
    <>
      <SectionHeader prompt="❯" title={<em>daily activity</em>} />
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 1,
        }}
      >
        implementation updates · last 30 days
      </Typography>
      <Box
        sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.25, height: 70, overflow: 'hidden' }}
      >
        {data.map(point => (
          <Tooltip key={point.date} title={`${point.date}: ${point.impls_updated} impls`} arrow>
            <Box
              sx={{
                flex: 1,
                height: `${Math.max((point.impls_updated / maxDaily) * 100, point.impls_updated > 0 ? 3 : 0)}%`,
                bgcolor: colors.primaryDark,
                opacity: 0.5,
                borderRadius: '2px 2px 0 0',
                minHeight: point.impls_updated > 0 ? 2 : 0,
                '&:hover': { opacity: 0.8 },
                transition: 'opacity 0.15s ease',
              }}
            />
          </Tooltip>
        ))}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.micro,
            color: semanticColors.mutedText,
          }}
        >
          {firstDate}
        </Typography>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.micro,
            color: semanticColors.mutedText,
          }}
        >
          {lastDate}
        </Typography>
      </Box>
    </>
  );
}
