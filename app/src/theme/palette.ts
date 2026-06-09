import type { ThemeOptions } from '@mui/material/styles';

import { colors } from 'src/theme/tokens';

// MUI's palette must be raw CSS colors (hex/rgb/hsl) — it calls decomposeColor
// internally for hover/alpha computations and rejects var(...) tokens.
// We pass the LIGHT hex values here; theme adaptation happens via CSS vars on
// explicitly-styled elements (and via the body color set in MuiCssBaseline).
export const palette: ThemeOptions['palette'] = {
  mode: 'light',
  primary: {
    main: colors.primary,
  },
  text: {
    primary: colors.gray[800],
    secondary: colors.gray[600],
  },
  background: {
    default: colors.background,
  },
};
