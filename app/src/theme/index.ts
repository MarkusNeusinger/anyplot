/**
 * Theme constants for anyplot frontend.
 *
 * Editorial/paper aesthetic with Okabe-Ito colorblind-safe palette.
 * Brand color: #009E73 (bluish green).
 * Warm off-white backgrounds, three font families.
 */

export const typography = {
  // MonoLisa with system mono fallback (size-adjusted to prevent CLS)
  fontFamily: '"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, "DejaVu Sans Mono", monospace',
  // Three font families for the editorial aesthetic
  serif: '"Fraunces", "Fraunces Fallback", Georgia, serif',
  sans: '"Inter", system-ui, sans-serif',
  mono: '"MonoLisa", "MonoLisa Fallback", "JetBrains Mono", Consolas, monospace',
} as const;

export const colors = {
  // Brand — Okabe-Ito palette
  primary: '#009E73', // Bluish green — brand anchor
  accent: '#E69F00', // Orange — badges, highlights

  // Okabe-Ito full palette (for direct reference)
  okabe: {
    green: '#009E73',
    vermillion: '#D55E00',
    blue: '#0072B2',
    purple: '#CC79A7',
    orange: '#E69F00',
    sky: '#56B4E9',
    yellow: '#F0E442',
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

  // Semantic colors — Okabe-Ito mapped
  success: '#009E73', // Green
  error: '#D55E00', // Vermillion
  warning: '#E69F00', // Orange
  info: '#0072B2', // Blue

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
  tooltipLight: '#56B4E9', // Sky blue on dark tooltip backgrounds

  // Code blocks (dark theme)
  codeBlock: {
    bg: '#0E0E0C',
    text: '#E8E8E0',
  },
} as const;

// Semantic text colors — WCAG AA safe on #F5F3EC backgrounds
export const semanticColors = {
  labelText: '#4A4A44', // --ink-soft — 7.2:1 on #F5F3EC, labels/categories
  subtleText: '#4A4A44', // --ink-soft — secondary/metadata text
  mutedText: '#8A8A82', // --ink-muted — 4.5:1, decorative/less critical text
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
  color: colors.gray[800],
  mb: 2,
} as const;

export const subheadingStyle = {
  fontFamily: typography.serif,
  fontWeight: 400,
  fontSize: fontSize.lg,
  color: colors.gray[600],
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

export const tableStyle = {
  '& .MuiTableCell-root': {
    fontFamily: typography.fontFamily,
    fontSize: fontSize.md,
    color: semanticColors.labelText,
    borderBottom: `1px solid ${colors.gray[200]}`,
    py: 1.5,
    px: 2,
  },
  '& .MuiTableCell-head': {
    fontWeight: 600,
    color: colors.gray[600],
    backgroundColor: colors.gray[50],
  },
} as const;
