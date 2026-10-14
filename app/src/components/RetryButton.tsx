import Box from '@mui/material/Box';

import { colors, typography } from 'src/theme';

interface RetryButtonProps {
  onClick: () => void;
  /** Accessible name; the visible label stays the method call `.retry()`. */
  label?: string;
}

/**
 * `.retry()` — the ghost method-call button (style guide §7.4) for a load that
 * still failed after apiGet's own retries. It re-runs the load in place, so a
 * transient edge glitch never needs a full page reload.
 */
export function RetryButton({ onClick, label = 'Retry loading' }: RetryButtonProps) {
  return (
    <Box
      component="button"
      type="button"
      aria-label={label}
      onClick={onClick}
      sx={{
        fontFamily: typography.mono,
        fontSize: '0.8125rem',
        fontWeight: 500,
        color: 'var(--ink)',
        bgcolor: 'transparent',
        border: '1px solid var(--rule)',
        borderRadius: '4px',
        px: 1.25,
        py: 0.75,
        minHeight: 32,
        cursor: 'pointer',
        whiteSpace: 'nowrap',
        transition: 'color 0.2s, background 0.2s, border-color 0.2s',
        '&:hover': {
          color: colors.primary,
          bgcolor: 'var(--bg-elevated)',
          borderColor: 'var(--ink-muted)',
        },
        '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
      }}
    >
      .retry()
    </Box>
  );
}
