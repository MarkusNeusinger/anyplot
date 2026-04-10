import React from 'react';
import ReactDOM from 'react-dom/client';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AppRouter } from './router';
import { reportWebVitals } from './analytics/reportWebVitals';
import { typography, colors, semanticColors, fontSize } from './theme';

// Import MonoLisa font - hosted on GCS (all text uses MonoLisa)
import './styles/fonts.css';

const theme = createTheme({
  typography: {
    fontFamily: typography.fontFamily,
  },
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary,
    },
    text: {
      primary: colors.gray[800],
      secondary: semanticColors.subtleText,
    },
    background: {
      default: colors.background,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: colors.background,
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
