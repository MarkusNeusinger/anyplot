import React from 'react';
import ReactDOM from 'react-dom/client';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AppRouter } from './router';
import { reportWebVitals } from './analytics/reportWebVitals';

// Import MonoLisa font - hosted on GCS (all text uses MonoLisa)
import './styles/fonts.css';

const theme = createTheme({
  typography: {
    fontFamily: '"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, monospace',
  },
  palette: {
    mode: 'light',
    primary: {
      main: '#3776AB', // Python blue
    },
    text: {
      primary: '#1f2937',
      secondary: '#52525b',
    },
    background: {
      default: '#fafafa',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#fafafa',
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
          fontFamily: '"MonoLisa", "MonoLisa Fallback", monospace',
          fontSize: '0.75rem',
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
