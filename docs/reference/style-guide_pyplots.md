# Style Guide

Design system for the anyplot.ai frontend. All values are defined in `app/src/theme/index.ts` and `app/src/main.tsx`.

## Colors

### Brand

| Token | Hex | Usage |
|-------|-----|-------|
| `colors.primary` | `#3776AB` | Python blue — primary brand, links, active states |
| `colors.accent` | `#FFD43B` | Python yellow — small accents only (logo, loader) |

### Gray Scale

| Token | Hex | Contrast on #fff | Usage |
|-------|-----|-------------------|-------|
| `gray.900` | `#111827` | 15.4:1 | — |
| `gray.800` | `#1f2937` | 13.5:1 | Primary text |
| `gray.700` | `#374151` | 10.3:1 | Headings, hover states |
| `gray.600` | `#4b5563` | 7.0:1 | Labels, categories |
| `gray.500` | `#6b7280` | 4.6:1 | Muted text, decorative icons |
| `gray.400` | `#9ca3af` | 2.9:1 | Borders, dividers, dashed outlines ONLY |
| `gray.300` | `#d1d5db` | — | Subtle borders, missing-data indicators |
| `gray.200` | `#e5e7eb` | — | Card borders, dividers |
| `gray.100` | `#f3f4f6` | — | Breadcrumb background, chips |
| `gray.50` | `#f9fafb` | — | Subtle backgrounds |

**Gray Usage Rule:** `gray.400` (#9ca3af) and lighter grays **must never be used for text or interactive icon colors**. They fail WCAG AA contrast requirements (2.9:1 vs required 4.5:1). Use `semanticColors.mutedText` (#6b7280, 4.6:1) as the minimum contrast for any text.

### Semantic Text Colors

WCAG AA requires 4.5:1 contrast for normal text, 3:1 for large text (>=18px or >=14px bold).

| Token | Hex | Contrast | Usage |
|-------|-----|----------|-------|
| `semanticColors.labelText` | `#4b5563` | 7.0:1 | Labels, tag categories, card labels |
| `semanticColors.subtleText` | `#52525b` | 5.8:1 | Secondary text, descriptions, metadata |
| `semanticColors.mutedText` | `#6b7280` | 4.6:1 | Decorative text, footer links, breadcrumb separators |

### Extended Brand

| Token | Hex | Usage |
|-------|-----|-------|
| `colors.primaryDark` | `#306998` | Python dark blue — dataviz bars, chart hover accents |
| `colors.accentBg` | `#fffef5` | Warm yellow-tinted background for accent sections |

### Highlight Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `colors.highlight.bg` | `#dbeafe` | Light blue background for highlighted tag chips |
| `colors.highlight.text` | `#1e40af` | Dark blue text for highlighted tag chips |
| `colors.tooltipLight` | `#90caf9` | Light blue text/links on dark tooltip backgrounds |

### Code Block Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `colors.codeBlock.bg` | `#1e293b` | Dark code block background |
| `colors.codeBlock.text` | `#e2e8f0` | Code block text on dark background |

Inline code uses `colors.gray[100]` background with `colors.primary` text color.

### Semantic Status

| Token | Hex | Usage |
|-------|-----|-------|
| `colors.success` | `#22c55e` | Success states, score >= 90 |
| `colors.error` | `#ef4444` | Error states, score < 50 |
| `colors.warning` | `#f59e0b` | Warnings, score 50-89 |
| `colors.info` | `#3b82f6` | Info states |

## Typography

### Font Family

```
"MonoLisa", "MonoLisa Fallback", Consolas, Menlo, Monaco, "DejaVu Sans Mono", monospace
```

MonoLisa is a premium monospace font loaded from GCS with unicode-range subsets. The fallback uses size-adjusted system monospace fonts (106.5% scale) to prevent layout shift.

### Font Scale

| Token | Size | Px (at 16px base) | Usage |
|-------|------|-------|-------|
| `fontSize.micro` | 0.5rem | 8px | Decorative axis labels, coverage legends (data-dense pages only) |
| `fontSize.xxs` | 0.625rem | 10px | Compact data values, secondary counts (data-dense pages only) |
| `fontSize.xs` | 0.75rem | 12px | Tiny labels, tag chips, keyboard hints |
| `fontSize.sm` | 0.8rem | 12.8px | Small text, shared tags, metadata footer |
| `fontSize.md` | 0.875rem | 14px | Body default, card labels, footer |
| `fontSize.base` | 0.9375rem | 15px | Primary body text, breadcrumb, filter chips |
| `fontSize.lg` | 1rem | 16px | Large text, category headers |
| `fontSize.xl` | 1.125rem | 18px | Titles, prominent text |

### Responsive Titles

| Element | xs | sm | md |
|---------|----|----|------|
| Logo (anyplot.ai) | 2rem | 2.75rem | 3.75rem |
| Spec page title | 1.375rem | 1.625rem | 2.125rem |
| Spec description | 0.875rem | 0.9375rem | — |

## Spacing

MUI spacing units (1 unit = 8px):

| Token | Units | Pixels | Usage |
|-------|-------|--------|-------|
| `spacing.xs` | 0.5 | 4px | Tight gaps |
| `spacing.sm` | 1 | 8px | Small gaps, chip spacing |
| `spacing.md` | 1.5 | 12px | Card padding, component gaps |
| `spacing.lg` | 2 | 16px | Section spacing |
| `spacing.xl` | 3 | 24px | Grid gaps, large sections |

## Responsive Breakpoints

MUI defaults:

| Name | Width | Typical Device |
|------|-------|---------------|
| xs | 0px | Mobile phones |
| sm | 600px | Tablets (portrait) |
| md | 900px | Tablets (landscape), small desktop |
| lg | 1200px | Desktop |
| xl | 1536px | Large desktop, ultrawide |

### Layout Container

```
padding-x: { xs: 16px, sm: 32px, md: 64px, lg: 96px, xl: 128px }
max-width: 2200px (centered)
```

### Content Max-Width (Spec Pages)

```
{ xs: 100%, md: 1200px, lg: 1400px, xl: 1800px }
```

### Grid Columns

| Context | xs | sm | md | lg | xl |
|---------|----|----|----|----|------|
| Home (normal) | 1 | 1 | 2 | 2 | 3 |
| Home (compact) | 2 | 2 | 4 | 4 | 6 |
| Spec overview | 1 | 2 | 3 | 3 | 3 |
| Related specs | Single row, auto-fit `minmax(130px, 1fr)`, overflow hidden |

## Components

### Cards (ImageCard)

- Border: `2px solid rgba(55, 118, 171, 0.3)`
- Border radius: 24px (MUI `borderRadius: 3`)
- Shadow: `0 2px 8px rgba(0,0,0,0.1)`
- Hover: border `0.4` opacity, shadow `0 8px 30px rgba(0,0,0,0.15)`, scale `1.03`
- Transition: `all 0.3s ease`
- Image aspect ratio: `16/10`
- Focus: `outline: none`, `focus-visible` only (no mouse focus ring)
- Copy confirmation: `>>> copied` overlay centered on image (dark bg, white text, 2s duration)

### Tag Chips

- Height: 24px
- Font: `fontSize.xs` (0.75rem)
- Default: `bgcolor: #f3f4f6`, `color: #4b5563`
- Highlighted: `bgcolor: #dbeafe`, `color: #1e40af`, `fontWeight: 600`
- Hover (clickable): `bgcolor: #e5e7eb`
- Tooltip: shows count of matching plots (e.g., `421 plots`), loaded once from `/plots/filter` globalCounts

### Library Pills

- Font: `fontSize.base` (0.9375rem)
- Active: `border: 1px solid #3776AB`, `fontWeight: 600`, `color: #374151`
- Inactive: `border: transparent`, `color: semanticColors.mutedText`
- Background: `#f3f4f6`

### Tooltips (global)

All tooltips share a consistent style defined in the MUI theme (`main.tsx`):

- Background: `rgba(0,0,0,0.8)`
- Font: MonoLisa monospace, `0.75rem`
- Padding: `4px 8px`
- Border radius: `4px`
- Enter delay: `200ms`
- Placement: `top` (default)
- Arrow color matches background

### Action Buttons (Copy, Download, Interactive)

- Background: `rgba(255,255,255,0.9)`
- Appear on card/image hover (`opacity: 0` -> `1`)
- Hover: `bgcolor: #fff`, `color: #3776AB` (Python blue highlight)
- Size: `small` (MUI IconButton)

### Toolbar Icons (Catalog, Grid Toggle)

- Size: `1.4rem` icons in `36px` hit targets
- Color: `semanticColors.mutedText` -> hover `#3776AB`
- Focus: `focus-visible` only (no mouse focus ring)

### Related Specs

- Grid: `auto-fit`, `minmax(130px, 1fr)`, single row with overflow hidden
- Cards that don't fit are hidden (no partial cards, no scrollbar)
- Library names abbreviated (`mpl`, `sns`, `ply`, etc.) with full name in tooltip
- Title and tag count have native tooltips for truncated text

## Animations

| Name | Duration | Easing | Usage |
|------|----------|--------|-------|
| Card fade-in | 0.4s | ease-out | First batch of image cards |
| Card hover | 0.3s | ease | Border, shadow, scale |
| Chip roll | 0.5s | ease-in/out | Filter chip add/remove |
| Shuffle wiggle | 0.8s | ease | Random button icon |
| Loader | 2s | linear | Loading spinner |

## Page Headings

Shared style constants are exported from `app/src/theme/index.ts`:

| Constant | Font Size | Weight | Color | Usage |
|----------|-----------|--------|-------|-------|
| `headingStyle` | 1.25rem | 600 | `gray.800` | Page section headings (h2) |
| `subheadingStyle` | `fontSize.lg` (1rem) | 600 | `gray.700` | Subsection headings (h3) |
| `textStyle` | `fontSize.base` (0.9375rem) | — | `labelText` | Body text paragraphs |

## Tables

Import `tableStyle` from theme for consistent table styling:

- Cell text: `semanticColors.labelText` (#4b5563)
- Cell font: `fontSize.md` (0.875rem)
- Header: `fontWeight: 600`, `color: gray.700`, `bgcolor: gray.50`
- Cell borders: `1px solid gray.100`

## Code Blocks

Import `codeBlockStyle` from theme for dark code blocks:

- Background: `colors.codeBlock.bg` (#1e293b)
- Text: `colors.codeBlock.text` (#e2e8f0)
- Font: `fontSize.md`, MonoLisa
- Inline code: `bgcolor: gray.100`, `color: colors.primary`, `padding: 4px 8px`, `borderRadius: 4px`

## Chart / DataViz Colors

| Element | Color Token | Usage |
|---------|------------|-------|
| Bar fills | `colors.primaryDark` | LOC histograms, timeline bars |
| Score >= 90 | `colors.success` | Green indicators |
| Score 50-89 | `colors.warning` | Yellow indicators |
| Score < 50 | `colors.error` | Red indicators |
| Missing/null | `colors.gray[200]` or `colors.gray[300]` | Background placeholder |
| Coverage heatmap | `rgba(34, 197, 94, opacity)` | Green gradient from 0.15 to 0.85 |

## Data-Dense Pages

StatsPage and DebugPage are internal data-dense pages that may use `fontSize.micro` and `fontSize.xxs` for compact data displays. These sizes are **not permitted** on public-facing pages (Home, Catalog, Spec, Legal, MCP).

## ErrorBoundary Exception

ErrorBoundary intentionally uses MUI defaults and raw `fontFamily: 'monospace'` as a crash-safe fallback. It must not depend on custom theme imports or MonoLisa font loading, since a font loading failure could have caused the crash.

## Accessibility

- All text must pass WCAG AA contrast (4.5:1 for normal, 3:1 for large)
- Never use `#9ca3af` or lighter for text on white/off-white backgrounds
- Interactive elements need visible focus states
- Images have descriptive `alt` text: `"{spec title} - {library}"`
- Keyboard navigation: arrow keys for library switching, Escape for lightbox
- Focus rings: `outline: none` on cards, `focus-visible` for keyboard-only focus indicators
- Tooltips: all interactive elements have descriptive tooltips
