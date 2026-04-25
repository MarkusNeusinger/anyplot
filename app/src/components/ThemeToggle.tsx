import Box from '@mui/material/Box';
import { colors, typography } from '../theme';
import type { ThemeMode } from '../hooks/useLayoutContext';

interface ThemeToggleProps {
  mode: ThemeMode;
  onCycle: () => void;
}

const NEXT_MODE: Record<ThemeMode, ThemeMode> = {
  system: 'light',
  light: 'dark',
  dark: 'system',
};

const ICON: Record<ThemeMode, string> = {
  system: '◑',
  light: '☀',
  dark: '☾',
};

export function ThemeToggle({ mode, onCycle }: ThemeToggleProps) {
  const next = NEXT_MODE[mode];
  return (
    <Box
      component="button"
      onClick={onCycle}
      aria-label={`Switch to ${next} theme`}
      title={`theme: ${mode}`}
      sx={{
        background: 'none',
        border: '1px solid var(--rule)',
        cursor: 'pointer',
        padding: { xs: '2px 6px', sm: '3px 9px' },
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
      {ICON[mode]}
      <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' }, ml: 0.5 }}>
        {mode}
      </Box>
    </Box>
  );
}
