import Box from '@mui/material/Box';
import { colors, typography } from '../theme';

interface NumbersStripProps {
  stats: { specs: number; plots: number; libraries: number } | null;
}

export function NumbersStrip({ stats }: NumbersStripProps) {
  const items = [
    { value: stats ? `${Math.floor(stats.plots / 1000)}k+` : '—', label: 'plotting examples', accent: true },
    { value: '09', label: 'libraries covered', accent: true },
    { value: '08', label: 'colors · Okabe-Ito', accent: true },
    { value: '03', label: 'CVD types safe', accent: true },
  ];

  return (
    <Box sx={{
      borderTop: '1px solid var(--rule)',
      borderBottom: '1px solid var(--rule)',
      py: 5,
      my: 5,
    }}>
      <Box sx={{
        maxWidth: 'var(--max)',
        mx: 'auto',
        display: 'grid',
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
        gap: 4,
      }}>
        {items.map((item, i) => (
          <Box key={i}>
            <Box sx={{
              fontFamily: typography.serif,
              fontSize: { xs: '2.5rem', md: '3.5rem' },
              fontWeight: 300,
              letterSpacing: '-0.03em',
              lineHeight: 1,
              color: item.accent ? colors.primary : 'var(--ink)',
              fontStyle: item.accent ? 'italic' : 'normal',
            }}>
              {item.value}
            </Box>
            <Box sx={{
              fontFamily: typography.mono,
              fontSize: '11px',
              color: 'var(--ink-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.12em',
              mt: 1,
            }}>
              {item.label}
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
