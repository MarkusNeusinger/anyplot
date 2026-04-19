import Box from '@mui/material/Box';
import { typography } from '../theme';

interface NumbersStripProps {
  stats: { specs: number; plots: number; libraries: number; lines_of_code?: number } | null;
}

function formatLoc(n: number | undefined): string {
  if (!n) return '—';
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return String(n);
}

export function NumbersStrip({ stats }: NumbersStripProps) {
  const items = [
    { value: '1', label: 'languages' },
    { value: stats ? String(stats.libraries) : '—', label: 'libraries' },
    { value: stats ? String(stats.specs) : '—', label: 'specifications' },
    { value: stats ? stats.plots.toLocaleString() : '—', label: 'implementations' },
    { value: formatLoc(stats?.lines_of_code), label: 'lines of code' },
  ];

  return (
    <Box sx={{
      borderTop: '1px solid var(--rule)',
      pt: { xs: 3, md: 3.5 },
      mt: { xs: 3, md: 2 },
      display: 'grid',
      gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(5, 1fr)' },
      gap: { xs: 4, md: 5 },
    }}>
      {items.map((item, i) => (
        <Box key={i}>
          <Box sx={{
            fontFamily: typography.mono,
            fontSize: { xs: '1.25rem', md: '1.5rem' },
            fontWeight: 600,
            letterSpacing: '-0.02em',
            lineHeight: 1,
            color: 'var(--ink-soft)',
          }}>
            {item.value}
          </Box>
          <Box sx={{
            fontFamily: typography.mono,
            fontSize: '12px',
            color: 'var(--ink-muted)',
            letterSpacing: '0.04em',
            mt: 0.75,
          }}>
            {item.label}
          </Box>
        </Box>
      ))}
    </Box>
  );
}
