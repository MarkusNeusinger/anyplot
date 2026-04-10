# Frontend Style Guide

All visual values are centralized in `app/src/theme/index.ts`. Never use hardcoded hex colors or font strings — always import tokens.

## Imports
```ts
import { typography, colors, semanticColors, fontSize, spacing } from '../theme';
// Shared style constants:
import { headingStyle, subheadingStyle, textStyle, codeBlockStyle, tableStyle, labelStyle, monoText } from '../theme';
```

## Colors
- **Brand**: `colors.primary` (#3776AB), `colors.accent` (#FFD43B), `colors.primaryDark` (#306998)
- **Gray scale**: `colors.gray[50]` to `colors.gray[900]`
- **Semantic text**: `semanticColors.labelText` (7.0:1), `semanticColors.subtleText` (5.8:1), `semanticColors.mutedText` (4.6:1)
- **Status**: `colors.success`, `colors.error`, `colors.warning`, `colors.info`
- **Backgrounds**: `colors.background`, `colors.accentBg`
- **Code blocks**: `colors.codeBlock.bg`, `colors.codeBlock.text`

## WCAG Rule
`colors.gray[400]` (#9ca3af) and lighter **must never be used for text or icons**. Minimum text color: `semanticColors.mutedText` (#6b7280, 4.6:1 contrast).

## Font
Always use `typography.fontFamily` — never inline `'"MonoLisa", monospace'` or raw `'monospace'`.
**Exception**: ErrorBoundary uses raw `'monospace'` intentionally (crash-safe fallback).

## Font Sizes
`fontSize.micro` (0.5rem) and `fontSize.xxs` (0.625rem) are restricted to data-dense pages (StatsPage, DebugPage).
Public pages use `fontSize.xs` (0.75rem) as minimum.
Full scale: micro, xxs, xs, sm, md, base, lg, xl.

## Shared Constants
- `headingStyle` — page h2 (1.25rem, 600, gray.800)
- `subheadingStyle` — page h3 (1rem, 600, gray.700)
- `textStyle` — body text (0.9375rem, labelText, lineHeight 1.8)
- `codeBlockStyle` — dark code blocks
- `tableStyle` — consistent table cells/headers
- `labelStyle` — small labels (0.875rem, labelText)

## Highlight Colors (not tokenized)
`#dbeafe`/`#1e40af` (highlighted tag chips) and `#90caf9` (tooltip text on dark bg) are intentionally kept as direct values.

## Full reference
See `docs/reference/style-guide.md` for complete documentation including spacing, breakpoints, component specs, animations, and accessibility rules.
