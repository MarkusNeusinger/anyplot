/**
 * Geometry of the floating bottom-right corner (px).
 *
 * The global FeedbackWidget FAB owns the corner. Anything else that floats
 * there (the quick-feedback stack, its "Thanks!" toast, the scroll-to-top
 * button on /plots and /specs) takes its position from these values, so the
 * pieces cannot drift into each other when one of them changes size.
 */

/** Feedback FAB distance from the right and bottom viewport edges. */
export const FAB_INSET = { xs: 12, sm: 16 } as const;
/** Feedback FAB diameter. */
export const FAB_SIZE = { xs: 40, sm: 48 } as const;
/** MUI `<Fab size="small">` diameter — quick-feedback buttons, scroll-to-top. */
export const MINI_FAB_SIZE = 40;
/** Gap between neighbouring floating buttons. */
export const FAB_GAP = 8;

// A mini FAB centred on the feedback FAB's axis, offset by that axis' inset.
const centredInset = (bp: keyof typeof FAB_INSET) =>
  FAB_INSET[bp] + (FAB_SIZE[bp] - MINI_FAB_SIZE) / 2;
// First free offset past the feedback FAB along one axis.
const pastFab = (bp: keyof typeof FAB_INSET) => FAB_INSET[bp] + FAB_SIZE[bp] + FAB_GAP;

/** Column above the feedback FAB — the quick-feedback stack and its toast. */
export const FAB_SLOT_ABOVE = {
  right: { xs: centredInset('xs'), sm: centredInset('sm') },
  bottom: { xs: pastFab('xs'), sm: pastFab('sm') },
} as const;

/** Row slot left of the feedback FAB, vertically centred on it — scroll-to-top. */
export const FAB_SLOT_LEFT = {
  right: { xs: pastFab('xs'), sm: pastFab('sm') },
  bottom: { xs: centredInset('xs'), sm: centredInset('sm') },
} as const;

/**
 * Distance of the FAB row's centre line from the viewport bottom on xs — the
 * pivot the footer lift aligns with the footer's top edge.
 */
export const FAB_ROW_CENTER_XS = FAB_INSET.xs + FAB_SIZE.xs / 2;
