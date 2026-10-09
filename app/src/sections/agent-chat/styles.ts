/**
 * Shared styles of the agent chat surfaces, after docs/reference/style-guide.md:
 * method-call buttons (§7.4), the filled CTA reserved for the one primary
 * action (`.create_plot()`), native form controls on the theme tokens, and the
 * panel surface. Colours come from the CSS variables, so both themes work.
 */

import { colors, fontSize, typography } from 'src/theme';

/** The smallest text on the chat surfaces: 13 px, the legibility floor at phone width. */
export const smallText = '0.8125rem';

/** `.verb()` action button: muted mono text, green on hover (§7.4). */
export const actionButtonSx = {
  fontFamily: typography.mono,
  fontSize: smallText,
  fontWeight: 500,
  color: 'var(--ink-soft)',
  bgcolor: 'transparent',
  border: 'none',
  borderRadius: '4px',
  px: 1.25,
  py: 0.75,
  minHeight: 32,
  cursor: 'pointer',
  whiteSpace: 'nowrap',
  transition: 'color 0.2s, background 0.2s',
  '&:hover:not(:disabled)': { color: colors.primary, bgcolor: 'var(--bg-elevated)' },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
  '&:disabled': { opacity: 0.45, cursor: 'default' },
} as const;

/** Filled CTA (§7.4 hero CTA): ink on paper, green on hover. One per surface. */
export const ctaButtonSx = {
  ...actionButtonSx,
  color: 'var(--bg-page)',
  bgcolor: 'var(--ink)',
  border: '1px solid transparent',
  px: 2,
  py: 1,
  '&:hover:not(:disabled)': { color: '#fff', bgcolor: colors.primary },
} as const;

/** Ghost button (§7.4): for a second action next to the CTA. */
export const ghostButtonSx = {
  ...actionButtonSx,
  color: 'var(--ink)',
  border: '1px solid var(--rule)',
  '&:hover:not(:disabled)': { color: colors.primary, borderColor: 'var(--ink-muted)' },
} as const;

/** Native input, textarea and select on the theme tokens. */
export const nativeControlSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.md,
  color: 'var(--ink)',
  bgcolor: 'var(--bg-elevated)',
  border: '1px solid var(--rule)',
  borderRadius: '4px',
  px: 1,
  py: 0.75,
  outline: 'none',
  minWidth: 0,
  '&:focus': { borderColor: colors.primary },
  '&:disabled': { opacity: 0.6 },
} as const;

/** A panel surface: the data panel and the chat. */
export const panelSx = {
  position: 'relative',
  bgcolor: 'var(--bg-surface)',
  border: '1px solid var(--rule)',
  borderRadius: 2,
  p: { xs: 1.5, sm: 2.5 },
  minWidth: 0,
} as const;

/** Small mono label above a control or a list. */
export const labelSx = {
  fontFamily: typography.mono,
  fontSize: smallText,
  color: 'var(--ink-muted)',
  letterSpacing: '0.02em',
} as const;

/** Body text inside the chat. */
export const bodyTextSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.md,
  color: 'var(--ink)',
  lineHeight: 1.6,
  overflowWrap: 'anywhere',
  whiteSpace: 'pre-wrap',
} as const;
