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
      main: '#2563eb', // Slightly softer blue
    },
    text: {
      primary: '#1f2937',
      secondary: '#6b7280',
    },
    background: {
      default: '#ffffff',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#ffffff',
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
