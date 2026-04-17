import Box from '@mui/material/Box';
import { typography } from '../theme';
import { ThemeToggle } from './ThemeToggle';
import { useTheme } from '../hooks';

/**
 * Top masthead bar (style-guide §6.4).
 *
 * Lowercase, monospace, three slots separated by │. Reads as a status line
 * from a tool — positions the site as a curated publication that lives
 * inside a terminal.
 */
export function MastheadRule() {
  const { isDark, toggle } = useTheme();

  return (
    <Box sx={{
      display: 'grid',
      gridTemplateColumns: '1fr auto 1fr',
      alignItems: 'center',
      py: 1.25,
      mb: 0,
      borderBottom: '1px solid var(--rule)',
      fontFamily: typography.mono,
      fontSize: '11px',
      color: 'var(--ink-muted)',
      letterSpacing: '0.04em',
    }}>
      <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
        ~/anyplot · v1 · spring 2026
      </Box>
      <Box sx={{
        px: 2,
        fontFeatureSettings: '"tnum"',
        textAlign: 'center',
        display: { xs: 'none', md: 'block' },
      }}>
        any library. one plot.
      </Box>
      <Box sx={{
        textAlign: 'right',
        gridColumn: { xs: '1 / -1', sm: 'auto' },
        display: 'flex',
        justifyContent: { xs: 'center', sm: 'flex-end' },
      }}>
        <ThemeToggle isDark={isDark} onToggle={toggle} />
      </Box>
    </Box>
  );
}
