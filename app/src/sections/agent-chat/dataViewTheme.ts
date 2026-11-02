/**
 * The MUI theme of the data panel's full view (`DataView.tsx`), one per site theme.
 *
 * The site's own theme stays in light mode and adapts through CSS variables
 * (`src/theme/palette.ts`), which MUI's palette cannot hold: it computes hover,
 * focus and border shades from raw colours. The Data Grid and the inputs,
 * menus and panels it opens take every colour from the palette, so the view
 * wraps them in a theme of the site's surfaces and inks in the theme the site
 * shows. The values are `src/styles/tokens.css`'s, pinned equal by a test.
 * Only the view's lazy chunk imports this module.
 */

import { createTheme, type Theme } from '@mui/material/styles';

import { components } from 'src/theme/components';
import { colors, typography } from 'src/theme/tokens';

export type SiteTheme = 'light' | 'dark';

/** `tokens.css`: `--bg-page`, `--bg-elevated`, `--ink`, `--ink-soft` and `--rule` of each theme. */
export const SITE_TOKENS: Record<SiteTheme, Record<string, string>> = {
  light: {
    '--bg-page': '#f5f3ec',
    '--bg-elevated': '#fffdf6',
    '--ink': '#1a1a17',
    '--ink-soft': '#4a4a44',
    '--rule': 'rgba(26, 26, 23, 0.15)',
  },
  dark: {
    '--bg-page': '#121210',
    '--bg-elevated': '#242420',
    '--ink': '#f0efe8',
    '--ink-soft': '#b8b7b0',
    '--rule': 'rgba(240, 239, 232, 0.15)',
  },
};

const themes: Partial<Record<SiteTheme, Theme>> = {};

export function dataViewTheme(mode: SiteTheme): Theme {
  const tokens = SITE_TOKENS[mode];
  themes[mode] ??= createTheme({
    // The preview table's mono at 13 px (`smallText`), for the cells, the inputs and the menus alike.
    typography: { fontFamily: typography.mono, body2: { fontSize: '0.8125rem' } },
    shape: { borderRadius: 4 },
    components,
    palette: {
      mode,
      primary: { main: colors.primary },
      error: { main: colors.error },
      text: { primary: tokens['--ink'], secondary: tokens['--ink-soft'] },
      background: { default: tokens['--bg-page'], paper: tokens['--bg-elevated'] },
      divider: tokens['--rule'],
    },
  });
  return themes[mode];
}
