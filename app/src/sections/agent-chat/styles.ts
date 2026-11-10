/**
 * Shared styles of the agent chat surfaces, after docs/reference/style-guide.md:
 * method-call buttons (§7.4), the composer row's plot button, the one filled button (the step's
 * action, the one place outside the landing hero that §7.4 allows it), the message
 * box, native form controls on the theme tokens, the chat frame (§7.9) with its header row's
 * chips and the actions of its foot, the panel and card surfaces, and the room the site's
 * masthead takes. Colours come from the CSS variables, so both themes work.
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

/** A button the click would not act on now: `disabled`, or `aria-disabled`, which keeps the focus. */
const INERT = '&:disabled, &[aria-disabled="true"]';
/** The hover of a button that acts. */
const ACTIVE_HOVER = '&:hover:not(:disabled):not([aria-disabled="true"])';

/**
 * The composer row's plot button (§7.4, §7.9), at least 44 px high in the text's size with a
 * small line under its name (`Composer.tsx`), one size in every state, ghost before there is data
 * and filled after. An inert one is `aria-disabled`: it dims,
 * its click does nothing and it keeps the keyboard focus.
 */
const composerButtonSx = {
  fontFamily: typography.mono,
  fontSize: fontSize.md,
  fontWeight: 500,
  border: '1px solid transparent',
  borderRadius: '4px',
  px: 1.5,
  py: 1,
  minHeight: 44,
  cursor: 'pointer',
  whiteSpace: 'nowrap',
  transition: 'color 0.2s, background 0.2s, border-color 0.2s',
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
  [INERT]: { opacity: 0.45, cursor: 'default' },
} as const;

/** The plot button before there is data: a ghost button, ink in the quiet rule, inert. */
export const composerGhostSx = {
  ...composerButtonSx,
  color: 'var(--ink)',
  bgcolor: 'transparent',
  borderColor: 'var(--rule)',
  [ACTIVE_HOVER]: { color: colors.primary, borderColor: 'var(--ink-muted)' },
} as const;

/**
 * The filled button (§7.4): ink on the page colour, green on hover. The chat has one, the plot
 * button from the moment data is stored (`.create_plot() →`, `.update_plot() →`, `plot the new
 * data`, or `.plot_all()`); before that, the data line above the box is the highlighted way in.
 */
export const composerFilledSx = {
  ...composerButtonSx,
  color: 'var(--bg-page)',
  bgcolor: 'var(--ink)',
  // The hover uses the light theme's ink in both themes: 14 px white text on the brand
  // green reads 3.4:1 and the dark theme's ink 3.0:1, under the 4.5:1 of WCAG AA, while
  // this dark foreground reads 5.1:1.
  [ACTIVE_HOVER]: { color: colors.gray[800], bgcolor: colors.primary },
} as const;

/**
 * An action at the end of the line at the chat frame's foot: `.stop()`, `.start_over()` and
 * `.feedback()`. The line's own small size, a 44 px target at phone width and 32 px from `sm` up.
 */
export const statusActionSx = {
  ...actionButtonSx,
  minHeight: { xs: 44, sm: 32 },
  '&:hover:not(:disabled)': {},
  [ACTIVE_HOVER]: { color: colors.primary, bgcolor: 'var(--bg-elevated)' },
  [INERT]: { opacity: 0.45, cursor: 'default' },
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

/**
 * The message box (§7.9): the one field that takes text, with the brand green as its boundary in
 * both themes, 3.1:1 against the light page and its own surface and more on the dark one, so it
 * stands out of the quiet frame (WCAG 1.4.11 asks 3:1 of a control's boundary). Green here is a
 * line, never text, so it needs no darker shade. The focus adds a ring in the same green.
 */
export const messageBoxSx = {
  ...nativeControlSx,
  border: `1px solid ${colors.primary}`,
  borderRadius: '6px',
  px: 1.25,
  py: 1.25,
  minHeight: 44,
  '&:focus': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
} as const;

/**
 * The chat frame (§7.9, `ChatFrame.tsx`): a terminal window on the page, after the hero's plot
 * panel (§7.1). One rule with a small radius on the page's own colour, so the tab label on its
 * top border punches through it, and the room above the frame that the label needs.
 */
export const frameSx = {
  position: 'relative',
  border: '1px solid var(--rule)',
  borderRadius: '6px',
  mt: 1.5,
  pt: { xs: 2.75, sm: 3.25 },
  px: { xs: 1.5, sm: 3 },
  pb: { xs: 1.5, sm: 1.75 },
  minWidth: 0,
} as const;

/** The dashed rule inside the frame: under the header row, and between the thread and the composer. */
export const frameRuleSx = { borderTop: '1px dashed var(--rule)' } as const;

/**
 * A dropdown chip of the header row (the library, the reply language): the value in plain words
 * and `▾`, a 40 px target on a wide screen and 44 px at phone width. The words name the control,
 * so its boundary is the quiet rule, as the frame's.
 */
export const headerChipSx = {
  ...actionButtonSx,
  fontSize: fontSize.md,
  display: 'inline-flex',
  alignItems: 'center',
  color: 'var(--ink)',
  bgcolor: 'var(--bg-elevated)',
  border: '1px solid var(--rule)',
  px: 1.25,
  minHeight: { xs: 44, sm: 40 },
  '&:hover:not(:disabled)': { color: colors.primary, borderColor: 'var(--ink-muted)' },
  '&:disabled': { opacity: 0.45, cursor: 'default' },
  '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
} as const;

/** A panel surface: the admin fan-out's panel below the chat frame. */
export const panelSx = {
  position: 'relative',
  bgcolor: 'var(--bg-surface)',
  border: '1px solid var(--rule)',
  borderRadius: 2,
  p: { xs: 1.5, sm: 2.5 },
  minWidth: 0,
} as const;

/** A card inside the thread, on the result card's surface: the admin fan-out's rows. */
export const cardSx = {
  border: '1px solid var(--rule)',
  borderRadius: 2,
  bgcolor: 'var(--bg-page)',
  p: { xs: 1.25, sm: 2 },
  minWidth: 0,
} as const;

/** Phone width, MUI's `xs`: the cards put their actions on a line of their own (`CardFrame.tsx`). */
export const PHONE_QUERY = '(max-width: 599.95px)';

/** A `.verb()` on a card's action line at phone width: a 44 px target for a thumb. */
export const cardActionSx = { ...actionButtonSx, minHeight: 44 } as const;

/**
 * A card of the thread in the v4 design (§7.9, `CardFrame.tsx`): the chat frame's construction
 * at a card's size, a 1 px rule with a 6 px radius on the page's own colour, so the label on its
 * top border punches through it. The room above it keeps the label, which stands half above the
 * border, clear of the item before the card.
 */
export const cardFrameSx = {
  position: 'relative',
  border: '1px solid var(--rule)',
  borderRadius: '6px',
  bgcolor: 'var(--bg-page)',
  mt: 1,
  pt: { xs: 2, sm: 2.25 },
  px: { xs: 1.25, sm: 1.5 },
  pb: { xs: 1.25, sm: 1.5 },
  minWidth: 0,
} as const;

/**
 * The room the site's sticky masthead takes at the top of the window
 * (`src/layouts/RootLayout.tsx`, 42 to 44 px high, z-index 100), with a gap: the
 * chat page's `scroll-padding-top`. A control that gets the keyboard focus, a
 * chapter a jump goes to and the data card the focus follows land below the
 * masthead, never under it (WCAG 2.4.11). A per-element `scroll-margin-top` is
 * not enough: Chrome's keyboard focus checks whether a control is in view
 * against the padded viewport only, so a control under the masthead counts as
 * in view and stays hidden.
 */
export const MASTHEAD_CLEARANCE = 56;

/** How long a jump's target keeps its highlight, in ms (the v4 mock's flash, `jumpTargetSx`). */
export const JUMP_MS = 1600;

/**
 * A place a jump lands on (a chapter's count of its questions, `ChapterLine.tsx`): while it holds
 * `data-jump`, a ring and a tint in the brand green show where the focus went, fading in and out
 * (the v4 mock's `.jump` and `.hl`), at once under `prefers-reduced-motion`, where the highlight
 * still shows. The ring is a line, never text, so it needs no darker green. A keyboard focus keeps
 * its own ring; a click's focus shows the highlight alone.
 */
export const jumpTargetSx = {
  transition: 'box-shadow 0.3s, background-color 0.3s',
  '&[data-jump]': {
    boxShadow: `0 0 0 2px ${colors.primary}`,
    bgcolor: 'rgba(0, 158, 115, 0.1)',
  },
  '&:focus': { outline: 'none' },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 3 },
  '@media (prefers-reduced-motion: reduce)': { transition: 'none' },
} as const;

/**
 * A control in a chapter's line (`ChapterLine.tsx`): its count of questions and the remembered
 * decisions' `N decisions ▾`, underlined words in the line's own size, as the v4 mock draws them;
 * a 32 px target at phone width, 24 px from `sm` up. The negative margin keeps the target out of
 * the line's height, into the thread's gaps above and below it, so a line keeps its height when its
 * first count comes and nothing below it moves. 32 px, not the cards' 44: a line that wraps on a
 * phone keeps its rows 12 px apart (`CHAPTER_ROW_GAP`), so two rows' targets meet and never overlap.
 */
export const chapterControlSx = {
  font: 'inherit',
  letterSpacing: 'inherit',
  color: 'inherit',
  bgcolor: 'transparent',
  border: 'none',
  borderRadius: '4px',
  p: 0,
  px: 0.25,
  minHeight: { xs: 32, sm: 24 },
  my: { xs: -0.75, sm: -0.25 },
  cursor: 'pointer',
  textDecoration: 'underline',
  textUnderlineOffset: '3px',
  whiteSpace: 'nowrap',
  '&:hover': { color: colors.primary },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
} as const;

/** The gap between the rows of a chapter's line that wraps (a phone), in theme spacing units. */
export const CHAPTER_ROW_GAP = 1.5;

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

/**
 * A readable line, at most about 80 characters: the thread's text and a result card's text
 * lists keep it since the chat column grows up to 1360 px (2026-11-02), while the data card,
 * the plot cards and the code take the full width.
 */
export const CHAT_TEXT_MAX = '80ch';
export const readableSx = { maxWidth: CHAT_TEXT_MAX } as const;

/**
 * The gap between the thread's items, and between the chat section's parts (the thread, the
 * foot with the progress timeline and the composer), in theme spacing units. The thread's
 * in-progress line offsets itself by their difference, so the timeline that follows it stands
 * where it stood (`ChatThread.tsx`).
 */
export const THREAD_GAP = 1.5;
export const CHAT_SECTION_GAP = 2;

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

/**
 * Inline code in the chat's text, such as a button the assistant names (`.undo()`): set off the
 * way the site's pages set off code (`McpPage`, `AboutPage`), so the backticks around it never
 * show.
 */
export const inlineCodeSx = {
  fontFamily: typography.mono,
  fontSize: '0.9em',
  bgcolor: 'var(--bg-elevated)',
  px: '4px',
  py: '1px',
  borderRadius: '3px',
  color: 'var(--ink)',
} as const;
