/**
 * Theme constants for anyplot frontend.
 *
 * Editorial/paper aesthetic with the anyplot imprint palette — a
 * colorblind-safe 8-hue categorical palette plus 3 semantic anchors
 * (amber for warning, theme-adaptive neutral and muted).
 * Brand color: #009E73 (bluish green, slot 0 — always first series).
 * Full design rationale: docs/reference/palette-variants-v3/decision-rationale.md
 */

export const typography = {
  // MonoLisa-only system — serif/sans kept as aliases so existing imports still resolve
  fontFamily: '"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, "DejaVu Sans Mono", monospace',
  serif: '"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, "DejaVu Sans Mono", monospace',
  sans: '"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, "DejaVu Sans Mono", monospace',
  mono: '"MonoLisa", "MonoLisa Fallback", "JetBrains Mono", Consolas, monospace',
} as const;

export const colors = {
  // Brand — imprint palette
  primary: '#009E73', // Brand green — slot 0, always first series
  accent: '#BD8233', // Ochre — badges, highlights (warm-neutral, plays well with brand green)

  // imprint full palette — 8 categorical hues in hybrid-v3 sort order
  imprint: {
    green: '#009E73',   // slot 0 — brand
    lavender: '#C475FD', // slot 1
    blue: '#4467A3',    // slot 2
    ochre: '#BD8233',   // slot 3
    red: '#AE3030',     // slot 4 — deferred semantic anchor for bad / loss / error
    cyan: '#2ABCCD',    // slot 5
    rose: '#954477',    // slot 6
    lime: '#99B314',    // slot 7
    // Semantic anchors outside the categorical pool
    amber: '#DDCC77',   // warning / caution (fixed hex)
    // neutral + muted are theme-adaptive — exposed as CSS vars below
  },

  // Gray scale — warm-tinted
  gray: {
    50: '#FAF8F1',
    100: '#F5F3EC',
    200: '#E8E6DF',
    300: '#D1CFC8',
    400: '#A5A39C',
    500: '#8A8A82',
    600: '#4A4A44',
    700: '#4A4A44',
    800: '#1A1A17',
    900: '#121210',
  },

  // Semantic colors — imprint mapped
  success: '#009E73', // brand green
  error: '#AE3030',   // matte red (slot 4 — the deferred semantic anchor)
  warning: '#DDCC77', // amber (semantic anchor, outside pool)
  info: '#4467A3',    // blue (slot 2)

  // Background — warm off-white
  background: '#F5F3EC',

  // Extended brand
  primaryDark: '#007A59', // Darker green — hover accents
  accentBg: '#FAF8F1', // Surface background

  // Highlights
  highlight: {
    bg: 'rgba(0, 158, 115, 0.12)', // Green-tinted highlight bg
    text: '#007A59', // Dark green text for highlighted chips
  },
  tooltipLight: '#2ABCCD', // Cyan on dark tooltip backgrounds

  // Code blocks — values come from CSS vars so they adapt with [data-theme]
  codeBlock: {
    bg: 'var(--code-bg)',
    text: 'var(--code-text)',
  },
} as const;

// Semantic text colors — adaptive via CSS vars (light/dark via [data-theme] in tokens.css)
// All pass WCAG AA on both --bg-page surfaces.
export const semanticColors = {
  labelText: 'var(--ink-soft)', // labels/categories
  subtleText: 'var(--ink-soft)', // secondary/metadata text
  mutedText: 'var(--ink-muted)', // decorative/less critical text
} as const;

export const fontSize = {
  micro: '0.5rem', // 8px — decorative axis/legend labels only
  xxs: '0.625rem', // 10px — data-dense dashboards (stats, debug)
  xs: '0.75rem',
  sm: '0.8rem',
  md: '0.875rem',
  base: '0.9375rem',
  lg: '1rem',
  xl: '1.125rem',
} as const;

export const spacing = {
  xs: 0.5,
  sm: 1,
  md: 1.5,
  lg: 2,
  xl: 3,
} as const;

// Common style patterns
export const monoText = {
  fontFamily: typography.fontFamily,
} as const;

export const labelStyle = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.md,
  color: semanticColors.labelText,
} as const;

// Page-level style constants — serif for editorial headings
export const headingStyle = {
  fontFamily: typography.serif,
  fontWeight: 400,
  fontSize: '1.25rem',
  color: 'var(--ink)',
  mb: 2,
} as const;

export const subheadingStyle = {
  fontFamily: typography.serif,
  fontWeight: 400,
  fontSize: fontSize.lg,
  color: 'var(--ink-soft)',
  mt: 3,
  mb: 1,
} as const;

export const textStyle = {
  fontFamily: typography.serif,
  fontSize: fontSize.base,
  fontWeight: 300,
  color: semanticColors.labelText,
  lineHeight: 1.8,
  mb: 2,
} as const;

export const codeBlockStyle = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.md,
  backgroundColor: colors.codeBlock.bg,
  color: colors.codeBlock.text,
  p: 2,
  borderRadius: 1,
  overflow: 'auto',
  mb: 2,
  whiteSpace: 'pre-wrap' as const,
  wordBreak: 'break-word' as const,
} as const;

// In-prose link style — default muted with 1px rule underline, hover flips to brand green.
// Applied to body-text anchors in About / Legal / MCP / editorial pages so brand green
// stays reserved for deliberate accent moments.
export const proseLinkStyle = {
  color: 'var(--ink-soft)',
  textDecoration: 'underline',
  textDecorationColor: 'var(--rule)',
  textDecorationThickness: '1px',
  textUnderlineOffset: '2px',
  transition: 'color 0.2s, text-decoration-color 0.2s',
  '&:hover': {
    color: colors.primary,
    textDecorationColor: colors.primary,
  },
} as const;

export const tableStyle = {
  '& .MuiTableCell-root': {
    fontFamily: typography.fontFamily,
    fontSize: fontSize.md,
    color: semanticColors.labelText,
    borderBottom: '1px solid var(--rule)',
    py: 1.5,
    px: 2,
  },
  '& .MuiTableCell-head': {
    fontWeight: 600,
    color: 'var(--ink-soft)',
    backgroundColor: 'var(--bg-surface)',
  },
} as const;
