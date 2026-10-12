/**
 * Shared styles of the debug page (`src/pages/DebugPage.tsx`) and its agent
 * cases section. Two text norms meet here: the page's data-dense lists use
 * 12 px (`fontSize.xs`, 10 px only for relative times), while the opened case
 * shows the agent chat's own content and keeps the chat's 13 px floor
 * (`smallText`).
 */

import { smallText } from 'src/sections/agent-chat/styles';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

/** Native input, select or button on the theme tokens, at the debug page's 12 px. */
export const debugControlSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xs,
  color: 'var(--ink)',
  bgcolor: 'var(--bg-surface)',
  border: '1px solid var(--rule)',
  borderRadius: '4px',
  px: 1,
  py: 0.75,
  outline: 'none',
  '&:focus': { borderColor: colors.primary },
  '&:disabled': { opacity: 0.6, cursor: 'default' },
} as const;

/** The same control at the opened case's 13 px floor. */
export const detailControlSx = { ...debugControlSx, fontSize: smallText } as const;

/** List text: 12 px, the debug page's norm. */
export const listTextSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xs,
  color: 'var(--ink)',
} as const;

/** Muted list text. */
export const listMutedSx = { ...listTextSx, color: semanticColors.mutedText } as const;

/** Text of the opened case: 13 px. */
export const detailTextSx = {
  fontFamily: typography.fontFamily,
  fontSize: smallText,
  color: 'var(--ink)',
  lineHeight: 1.55,
} as const;

/** Muted text of the opened case. */
export const detailMutedSx = { ...detailTextSx, color: semanticColors.mutedText } as const;

/** A `# heading` above a block of the opened case. */
export const detailLabelSx = {
  fontFamily: typography.mono,
  fontSize: smallText,
  color: 'var(--ink-muted)',
  letterSpacing: '0.02em',
  mb: 0.75,
} as const;

/** A small marker chip (`promoted`, `superseded`, a tag) in the list. */
export const chipSx = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 0.5,
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xs,
  lineHeight: 1.4,
  color: 'var(--ink-soft)',
  border: '1px solid var(--rule)',
  borderRadius: '4px',
  px: 0.75,
  whiteSpace: 'nowrap',
} as const;
