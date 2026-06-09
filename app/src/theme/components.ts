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
