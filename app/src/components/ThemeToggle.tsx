import Box from '@mui/material/Box';
import { colors, typography } from '../theme';

interface ThemeToggleProps {
  isDark: boolean;
  onToggle: () => void;
}

export function ThemeToggle({ isDark, onToggle }: ThemeToggleProps) {
  return (
    <Box
      component="button"
      onClick={onToggle}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      sx={{
        background: 'none',
        border: '1px solid var(--rule)',
        cursor: 'pointer',
        padding: '3px 9px',
        borderRadius: '4px',
        fontFamily: typography.mono,
        fontSize: '11px',
        letterSpacing: '0.02em',
        color: 'var(--ink-muted)',
        textTransform: 'none',
        transition: 'color 0.2s, border-color 0.2s',
        '&:hover': {
          color: colors.primary,
          borderColor: 'var(--ink-muted)',
        },
      }}
    >
      {isDark ? '☀ light' : '◐ dark'}
    </Box>
  );
}
