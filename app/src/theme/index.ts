/**
 * Theme constants for anyplot frontend.
 *
 * Centralized styling values to avoid hardcoded repetition.
 */

export const typography = {
  // MonoLisa with system mono fallback (size-adjusted to prevent CLS)
  fontFamily: '"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, "DejaVu Sans Mono", monospace',
} as const;

export const colors = {
  // Brand colors
  primary: '#3776AB', // Python blue
  accent: '#FFD43B', // Python yellow

  // Gray scale
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },

  // Semantic colors
  success: '#22c55e',
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',

  // Background
  background: '#fafafa',

  // Extended brand
  primaryDark: '#306998', // Python dark blue — dataviz bars, hover accents
  accentBg: '#fffef5', // Warm yellow-tinted bg for accent sections

  // Highlights
  highlight: {
    bg: '#dbeafe', // Light blue bg for highlighted chips
    text: '#1e40af', // Dark blue text for highlighted chips
  },
  tooltipLight: '#90caf9', // Light blue text on dark tooltip backgrounds

  // Code blocks (dark theme)
  codeBlock: {
    bg: '#1e293b',
    text: '#e2e8f0',
  },
} as const;

// Semantic text colors — WCAG AA safe on #fafafa/#fff backgrounds
export const semanticColors = {
  labelText: '#4b5563', // gray.600 — 7.0:1 on white, labels/categories
  subtleText: '#52525b', // ~5.8:1 on white, secondary/metadata text
  mutedText: '#6b7280', // gray.500, 4.6:1 — decorative/less critical text
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

// Page-level style constants
export const headingStyle = {
  fontFamily: typography.fontFamily,
  fontWeight: 600,
  fontSize: '1.25rem',
  color: colors.gray[800],
  mb: 2,
} as const;

export const subheadingStyle = {
  fontFamily: typography.fontFamily,
  fontWeight: 600,
  fontSize: fontSize.lg,
  color: colors.gray[700],
  mt: 3,
  mb: 1,
} as const;

export const textStyle = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.base,
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

export const tableStyle = {
  '& .MuiTableCell-root': {
    fontFamily: typography.fontFamily,
    fontSize: fontSize.md,
    color: semanticColors.labelText,
    borderBottom: `1px solid ${colors.gray[100]}`,
    py: 1.5,
    px: 2,
  },
  '& .MuiTableCell-head': {
    fontWeight: 600,
    color: colors.gray[700],
    backgroundColor: colors.gray[50],
  },
} as const;
