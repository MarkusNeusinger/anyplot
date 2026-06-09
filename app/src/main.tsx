// Import design tokens (CSS custom properties for theming + dark mode)
import './styles/tokens.css';
// Import web fonts - MonoLisa from GCS, Fraunces + Inter from Google Fonts
import './styles/fonts.css';

import React from 'react';
import ReactDOM from 'react-dom/client';

import CssBaseline from '@mui/material/CssBaseline';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import { reportWebVitals } from './analytics/reportWebVitals';
import { AppRouter } from './router';
import { colors, fontSize, typography } from './theme';

const theme = createTheme({
  typography: {
    fontFamily: typography.fontFamily,
  },
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary,
    },
    // MUI's palette must be raw CSS colors (hex/rgb/hsl) — it calls decomposeColor
    // internally for hover/alpha computations and rejects var(...) tokens.
    // We pass the LIGHT hex values here; theme adaptation happens via CSS vars on
    // explicitly-styled elements (and via the body color set in MuiCssBaseline below).
    text: {
      primary: '#1A1A17',
      secondary: '#4A4A44',
    },
    background: {
      default: '#F5F3EC',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
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
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppRouter />
    </ThemeProvider>
  </React.StrictMode>
);

reportWebVitals();
