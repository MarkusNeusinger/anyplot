import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { formatNum } from 'src/sections/debug/debugFormat';
import { fontSize, semanticColors, typography } from 'src/theme';

export interface KPIItem {
  label: string;
  value: number | null;
  suffix?: string;
}

export function KPIGrid({ kpis }: { kpis: KPIItem[] }) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(6, 1fr)' },
        gap: 2,
        mb: 4,
      }}
    >
      {kpis.map(item => (
        <Box
          key={item.label}
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
            {typeof item.value === 'number' ? `${formatNum(item.value)}${item.suffix ?? ''}` : '—'}
          </Typography>
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: fontSize.xs,
              color: semanticColors.mutedText,
              mt: 0.5,
            }}
          >
            {item.label}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}
