/**
 * Shared styles of the agent chat surfaces, after docs/reference/style-guide.md:
 * method-call buttons (§7.4), the filled CTA reserved for the one primary
 * action (`.create_plot()`, the one place outside the landing hero that §7.4
 * allows it), native form controls on the theme tokens, the panel and card
 * surfaces, and the pinned data header's offset and clearance. Colours come
 * from the CSS variables, so both themes work.
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

/** Ghost button (§7.4): for a second action next to the CTA. */
export const ghostButtonSx = {
  ...actionButtonSx,
  color: 'var(--ink)',
  border: '1px solid var(--rule)',
  '&:hover:not(:disabled)': { color: colors.primary, borderColor: 'var(--ink-muted)' },
} as const;

/**
 * The filled CTA (§7.4): ink on the page colour, green on hover. The chat has
 * one, `.create_plot()` in step 2, the action the whole page leads to.
 */
export const ctaButtonSx = {
  ...actionButtonSx,
  fontSize: fontSize.md,
  color: 'var(--bg-page)',
  bgcolor: 'var(--ink)',
  border: '1px solid transparent',
  px: 2,
  py: 1,
  // The hover uses the light theme's ink in both themes: 14 px white text on the brand
  // green reads 3.4:1 and the dark theme's ink 3.0:1, under the 4.5:1 of WCAG AA, while
  // this dark foreground reads 5.1:1.
  '&:hover:not(:disabled)': { color: colors.gray[800], bgcolor: colors.primary },
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

/** A panel surface: the chat column. */
export const panelSx = {
  position: 'relative',
  bgcolor: 'var(--bg-surface)',
  border: '1px solid var(--rule)',
  borderRadius: 2,
  p: { xs: 1.5, sm: 2.5 },
  minWidth: 0,
} as const;

/** A card inside the thread, on the result card's surface: the data card. */
export const cardSx = {
  border: '1px solid var(--rule)',
  borderRadius: 2,
  bgcolor: 'var(--bg-page)',
  p: { xs: 1.25, sm: 2 },
  minWidth: 0,
} as const;

/**
 * Where the pinned data header sticks: just under the site's sticky masthead
 * (`src/layouts/RootLayout.tsx`, 42 to 44 px high, z-index 100). A few pixels
 * less than its height, so the masthead covers the header's top edge instead of
 * leaving a gap the thread shows through.
 */
export const PINNED_TOP = 40;

/**
 * The room the masthead and the pinned data header take at the top of the
 * window (the header is 42 to 49 px high, two lines at phone width), with a gap.
 * While the header shows, the page's `scroll-padding-top`: a control that gets
 * the keyboard focus, or a card brought into view, lands below the header, never
 * under it (WCAG 2.4.11). A per-element `scroll-margin-top` is not enough:
 * Chrome's keyboard focus checks whether a control is in view against the
 * padded viewport only. The header's own toggle sits in the padding where it
 * sticks, so code focuses it with `preventScroll`.
 */
export const PINNED_CLEARANCE = PINNED_TOP + 64;

/** Read by screen readers, invisible on screen. */
export const visuallyHiddenSx = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  p: 0,
  m: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap',
  border: 0,
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
