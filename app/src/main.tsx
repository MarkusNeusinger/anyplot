// Import design tokens (CSS custom properties for theming + dark mode)
import 'src/styles/tokens.css';
// Import web fonts - MonoLisa Code + Text from GCS (no Google Fonts)
import 'src/styles/fonts.css';

import React from 'react';
import ReactDOM from 'react-dom/client';

import { reportWebVitals } from 'src/analytics/reportWebVitals';
import { App } from 'src/app';
import { watchShellDefaults } from 'src/utils/shellMetadata';

// The shell's default title and description stay as the fallback for every state in which a
// route renders none of its own, and step aside while one does.
watchShellDefaults();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

reportWebVitals();
