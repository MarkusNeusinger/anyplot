import Box from '@mui/material/Box';
import { typography } from '../theme';
import { ThemeToggle } from './ThemeToggle';
import { useTheme } from '../hooks';

export function MastheadRule() {
  const { isDark, toggle } = useTheme();

  return (
    <Box sx={{
      display: 'grid',
      gridTemplateColumns: '1fr auto 1fr',
      alignItems: 'center',
      py: 1.5,
      mb: 4,
      borderBottom: '1px solid var(--rule)',
      fontFamily: typography.mono,
      fontSize: '11px',
      color: 'var(--ink-muted)',
      textTransform: 'uppercase',
      letterSpacing: '0.12em',
    }}>
      <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
        Vol. 1 · 2026
      </Box>
      <Box sx={{
        px: 2,
        fontFeatureSettings: '"tnum"',
        textAlign: 'center',
        display: { xs: 'none', md: 'block' },
      }}>
        anyplot.ai — a catalogue of scientific plotting
      </Box>
      <Box sx={{ textAlign: 'right', gridColumn: { xs: '1 / -1', sm: 'auto' }, display: 'flex', justifyContent: { xs: 'center', sm: 'flex-end' } }}>
        <ThemeToggle isDark={isDark} onToggle={toggle} />
      </Box>
    </Box>
  );
}
