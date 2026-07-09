import type { ThemeOptions } from '@mui/material/styles';

import { fontSize, typography } from 'src/theme/tokens';

export const components: ThemeOptions['components'] = {
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        backgroundColor: 'var(--bg-page)',
        color: 'var(--ink)',
        transition: 'background-color 0.3s, color 0.3s',
      },
    },
  },
  // Stock MUI components fall back to the light-mode palette hexes (the MUI
  // palette can't hold var(...) tokens — see palette.ts). Wire the handful of
  // stock components we render to the CSS-var system so they adapt to
  // [data-theme='dark'] like everything else.
  MuiTab: {
    styleOverrides: {
      root: {
        color: 'var(--ink-soft)',
      },
    },
  },
  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: 'var(--rule)',
        // Dividers with children render their lines via ::before/::after,
        // which carry their own borderTop — the root borderColor alone
        // doesn't reach them.
        '&::before, &::after': {
          borderColor: 'var(--rule)',
        },
      },
    },
  },
  MuiSkeleton: {
    styleOverrides: {
      root: {
        backgroundColor: 'var(--rule)',
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        backgroundColor: 'var(--bg-elevated)',
        color: 'var(--ink)',
        border: '1px solid var(--rule)',
      },
    },
  },
  MuiTooltip: {
    defaultProps: {
      enterDelay: 200,
      placement: 'top' as const,
    },
    styleOverrides: {
      tooltip: {
        backgroundColor: 'rgba(0,0,0,0.8)',
        fontFamily: typography.fontFamily,
        fontSize: fontSize.xs,
        padding: '4px 8px',
        borderRadius: 4,
      },
      arrow: {
        color: 'rgba(0,0,0,0.8)',
      },
    },
  },
};
