// Import design tokens (CSS custom properties for theming + dark mode)
import 'src/styles/tokens.css';
// Import web fonts - MonoLisa from GCS, Fraunces + Inter from Google Fonts
import 'src/styles/fonts.css';

import React from 'react';
import ReactDOM from 'react-dom/client';

import { reportWebVitals } from 'src/analytics/reportWebVitals';
import { App } from 'src/app';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

reportWebVitals();
