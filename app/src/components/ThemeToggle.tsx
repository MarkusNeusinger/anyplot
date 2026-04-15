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
        border: `1px solid ${colors.gray[200]}`,
        cursor: 'pointer',
        padding: '4px 10px',
        borderRadius: '99px',
        fontFamily: typography.mono,
        fontSize: '10px',
        letterSpacing: '0.12em',
        color: colors.gray[500],
        textTransform: 'uppercase',
        transition: 'all 0.2s',
        '&:hover': {
          color: colors.gray[800],
          borderColor: colors.gray[800],
        },
      }}
    >
      {isDark ? '☀ light' : '◐ dark'}
    </Box>
  );
}
