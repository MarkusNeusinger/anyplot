/**
 * A card of the agent chat's thread in the v4 design (style guide §7.9): a 1 px rule with the
 * card's label on its top border, the chat frame's tab-label construction at a card's size
 * (`ChatFrame.tsx`). The label says what the card holds: a data version's number, how it came
 * about and its shape (`data v3 · made long · 48 rows × 4 cols`), or a plot card's version, library
 * and request (`plot v2 · matplotlib · title in German`).
 *
 * A plot card and an older data version fold, and then the label is the toggle: open, the card's
 * content stands under the label on the border; folded, the card is that label alone, one line in
 * the thread's flow with `▸` before it. It is the same button in both, in the same place of the
 * tree, so a click leaves the keyboard focus on it. Its name keeps the label's words in their
 * order (`Plot v2, matplotlib, title in German`, WCAG 2.5.3), the `·` read badly, and
 * `aria-expanded` says whether the card is open; the name stays the same in both states. A label
 * that names no control (the live data card's) is read out in words instead: `Data v3, made long,
 * 48 rows by 4 columns`.
 *
 * On the border the label stays on one line and ends in an ellipsis where the card is too narrow
 * for it (a long request on a phone); the folded line wraps instead.
 *
 * A label that names no control can still take the focus from code (`labelRef`): the live data
 * card puts it there when the control the user pressed went with the version it made
 * (`useFollowFocus`).
 */

import Box from '@mui/material/Box';

import {
  actionButtonSx,
  cardFrameSx,
  labelSx,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, typography } from 'src/theme';

/** The label on the border: half above it, on the page's colour, so it punches through the rule. */
const borderLabelSx = {
  ...labelSx,
  position: 'absolute',
  top: 0,
  left: { xs: 8, sm: 10 },
  transform: 'translateY(-50%)',
  px: 0.75,
  bgcolor: 'var(--bg-page)',
  color: 'var(--ink-soft)',
  lineHeight: '24px',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: { xs: 'calc(100% - 16px)', sm: 'calc(100% - 20px)' },
} as const;

/**
 * A label the focus can land on from code: the toggle's focus ring, no hover, since it does
 * nothing. The ring shows on every focus, not only a keyboard one: the focus lands here after the
 * card moved, also after a mouse click, and the ring shows where the card went (WCAG 2.4.7).
 */
const focusableLabelSx = {
  ...borderLabelSx,
  borderRadius: '4px',
  '&:focus': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
} as const;

/** The label as a toggle on the border: the same place, a button's hover and focus ring. */
const borderToggleSx = {
  ...borderLabelSx,
  display: 'block',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  textAlign: 'left',
  '&:hover': { color: colors.primary },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
} as const;

/** A folded card: its label as one line in the flow, the thread's quiet ink, a toggle to open it. */
const foldedLineSx = {
  ...actionButtonSx,
  display: 'block',
  maxWidth: '100%',
  px: 0.5,
  ml: -0.5,
  minHeight: { xs: 44, sm: 32 },
  fontWeight: 400,
  fontSize: fontSize.md,
  fontFamily: typography.mono,
  textAlign: 'left',
  whiteSpace: 'normal',
  overflowWrap: 'anywhere',
} as const;

export interface CardFrameToggle {
  /** Whether the card is open; folded, it is its label alone. */
  expanded: boolean;
  onToggle: () => void;
  /** The id of the open card's content, which the label controls. */
  bodyId: string;
}

export interface CardFrameProps {
  component?: 'section' | 'article' | 'div';
  /** The label on the border, and the folded card's line. */
  label: string;
  /** The label in words for a screen reader: the toggle's name, or read in place of the label. */
  spokenLabel?: string;
  /** A card that folds: its label is the toggle. Without it the card is always open. */
  toggle?: CardFrameToggle;
  /** The test id of the label, for the page's tests. */
  labelTestId?: string;
  /**
   * The label of a card that does not fold, as a target for the focus from code (`tabIndex` -1):
   * never in the tab order, since it names no control.
   */
  labelRef?: React.Ref<HTMLElement>;
  ref?: React.Ref<HTMLElement>;
  id?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
  'aria-live'?: 'off' | 'polite' | 'assertive';
  'data-testid'?: string;
  /** The focus entering and leaving the card, its label and content included (`useFollowFocus`). */
  onFocus?: React.FocusEventHandler<HTMLElement>;
  onBlur?: React.FocusEventHandler<HTMLElement>;
  children?: React.ReactNode;
}

export function CardFrame({
  component = 'div',
  label,
  spokenLabel,
  toggle,
  labelTestId,
  labelRef,
  children,
  ...rest
}: CardFrameProps) {
  const open = !toggle || toggle.expanded;
  const labelNode = toggle ? (
    <Box
      component="button"
      type="button"
      data-testid={labelTestId}
      onClick={toggle.onToggle}
      aria-expanded={toggle.expanded}
      aria-controls={toggle.expanded ? toggle.bodyId : undefined}
      aria-label={spokenLabel}
      sx={toggle.expanded ? borderToggleSx : foldedLineSx}
    >
      {!toggle.expanded && (
        <Box component="span" aria-hidden sx={{ mr: 0.75 }}>
          ▸
        </Box>
      )}
      {label}
    </Box>
  ) : (
    <Box
      component="span"
      data-testid={labelTestId}
      ref={labelRef}
      tabIndex={labelRef ? -1 : undefined}
      sx={labelRef ? focusableLabelSx : borderLabelSx}
    >
      {spokenLabel ? (
        <>
          <span aria-hidden>{label}</span>{' '}
          <Box component="span" sx={visuallyHiddenSx}>
            {spokenLabel}
          </Box>
        </>
      ) : (
        label
      )}
    </Box>
  );
  return (
    <Box component={component} {...rest} sx={open ? cardFrameSx : { minWidth: 0 }}>
      {labelNode}
      {open &&
        (toggle ? (
          <Box id={toggle.bodyId} sx={{ minWidth: 0 }}>
            {children}
          </Box>
        ) : (
          children
        ))}
    </Box>
  );
}
