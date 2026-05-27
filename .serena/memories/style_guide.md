# anyplot Design System

Canonical source: `docs/reference/style-guide.md` (brand · frontend · plots in one doc).
Frontend tokens: `app/src/theme/index.ts` + `app/src/main.tsx` (MUI theme).

## Aesthetic anchor
`arXiv paper` × `tmux/lazygit` — **the site is the neutral frame; the plots are the content.** Three layers: Brand (identity/voice), Frontend (visual language), Plots (color palette across all 9 libraries).

## Typography — MonoLisa only, one face + two voices
- **Roman (upright MonoLisa)** — default for everything: body, UI, nav, buttons, code, logo, display.
- **Script (italic MonoLisa + `ss02`)** — editorial accent, semantic emphasis only (hero sub-headlines, section titles, `<em>your</em>`, taglines).
- `ss02` is enabled globally on `html`: `font-feature-settings: "ss02";` — it only affects `font-style: italic`.
- **No second font.** Fraunces, Inter, Space Grotesk, Poppins are all out. The anti-pattern "reaching for a serif for warmth" explicitly forbidden.
- CSS vars `--serif`, `--sans`, `--mono` all resolve to the same MonoLisa stack (aliased for compatibility).
- **Exception**: ErrorBoundary uses raw `'monospace'` (crash-safe fallback).
- `fontSize.micro` (0.5rem) and `fontSize.xxs` (0.625rem) restricted to data-dense pages (StatsPage, DebugPage). Public pages: `fontSize.xs` (0.75rem) minimum.

## Color — imprint palette
Colourblind-safe categorical palette (8 hues, hybrid-v3 sort) plus 3 semantic anchors outside the pool. All 8 categorical slots stay fixed across themes; the neutral and muted anchors flip per theme. Full rationale: `docs/reference/palette-variants-v3/decision-rationale.md`.

```
slot 0 #009E73 brand green   ★ first series — logo, primary CTAs
slot 1 #C475FD lavender       (creative / artistic)         PLOT-ONLY
slot 2 #4467A3 blue            (info links, footnotes)
slot 3 #BD8233 ochre           (hover accent, earth / commodity)
slot 4 #AE3030 matte red       (errors, destructive — deferred semantic anchor)
slot 5 #2ABCCD cyan            (sky / tech-cool)            PLOT-ONLY
slot 6 #954477 rose            (wellness / health)          PLOT-ONLY
slot 7 #99B314 lime            (growth / nature)            PLOT-ONLY

semantic anchors (outside the categorical pool):
  amber   #DDCC77             warning / caution (fixed)
  neutral #1A1A17 / #F0EFE8   totals / baseline / outline (theme-adaptive)
  muted   #6B6A63 / #A8A79F   other / rest / disabled    (theme-adaptive)
```

**Brand green `#009E73` appears in UI ONLY in 8 contexts:** logo dot, italic accent words in headlines, hero terminal cursor, active nav item (dot prefix + underline), code-action button hover, code-block syntax (comments), palette strip, small status indicators.
**Never**: backgrounds, regular card borders, body text emphasis, non-logo icons, static decorative dots.

**Plot-only colours** (lavender, cyan, rose, lime) must never appear in UI chrome — they are reserved for data marks so categorical plots retain visual impact.

## Surfaces — warm, not clinical
Pure `#FFFFFF` is out — makes saturated palette colors look harsh.

| Token          | Light     | Dark      |
|----------------|-----------|-----------|
| `--bg-page`    | `#F5F3EC` | `#121210` |
| `--bg-surface` | `#FAF8F1` | `#1A1A17` |
| `--bg-elevated`| `#FFFDF6` | `#242420` |

## Warm-tinted grayscale (reddish-brown undertone, not blue-gray)
| Token          | Light     | Dark      | Role             |
|----------------|-----------|-----------|------------------|
| `--ink`        | `#1A1A17` | `#F0EFE8` | Primary text     |
| `--ink-soft`   | `#4A4A44` | `#B8B7B0` | Secondary text   |
| `--ink-muted`  | `#8A8A82` | `#6E6D66` | Tertiary, meta   |
| `--rule`       | rgba(26,26,23,.10) | rgba(240,239,232,.10) | Borders/dividers |

## WCAG rule
`colors.gray[400]` (#9ca3af) and lighter **must never be used for text or icons**. Minimum text color = `semanticColors.mutedText` (#6b7280, 4.6:1).

## Frontend imports (MUI theme)
```ts
import { typography, colors, semanticColors, fontSize, spacing } from '../theme';
import { headingStyle, subheadingStyle, textStyle, codeBlockStyle, tableStyle, labelStyle, monoText } from '../theme';
```
Semantic text tokens: `labelText` 7.0:1, `subtleText` 5.8:1, `mutedText` 4.6:1.
Highlight treatments: `colors.highlight.bg`/`colors.highlight.text`, `colors.tooltipLight` — never hardcode highlight hex.

## Layout — three tiers
- **paper** 1240px — landing hero, About, Methodology, Blog, Legal
- **catalog** 2200px — plot catalog, search results, library/spec pages
- **hero-flank** 100vw — ultrawide-only (`≥1600px`) vertical plot stacks
- Gutter: 24px mobile → 96px wide. Section padding: 80px vertical desktop. Card padding: 24–28px.

## Section-header pattern (shell-prompt prefixes)
- `❯` navigation/categorical · `$` action/list · `~/path/` hierarchical/about
- Title in italic + ss02 (script), `--imprint-green`, underlined with 1px `--rule`.

## Buttons — method-call doctrine
- **Action** (primary affordance): `.copy()`, `.open()`, `.download()` — `::before { content: "." }`, hover flips to `--imprint-green`.
- **Hero CTA** (filled, landing only): dark pill, 4px radius, hover → green.
- **Ghost** (rare): transparent, `--rule` border.

## Logo `any.plot()`
MonoLisa Bold, letters `--ink`, `.` `--imprint-green` scaled 1.3× (circle), `()` `--ink` weight 400 at 45% opacity. Favicon reduces to `a.p`. Clear space `1em`.

## Voice
Precise · understated · curious · respectful · slightly playful · code-native · AI-honest.
Avoid: sales-y ("unlock", "supercharge"), corporate ("solutions", "leverage"), breathless, AI-hype ("AI-powered", "intelligent"), emoji-heavy.
Default: **lowercase**. Oxford comma always. Em-dashes with spaces (European style).
AI pipeline framing: humans submit ideas + approve specs + tune rules; AI drafts specs, generates code, reviews. Never patch generated code by hand.

## Anti-patterns
Gradients (esp. purple-blue SaaS), glass/backdrop-blur, isometric illustrations, parallax/hero videos, badge-heavy UI, pure `#FFF`/`#000` backgrounds, branded spinners, stock imagery, **second typeface**, categorical palettes on continuous data.

## Plot defaults
- First series **always** `#009E73`.
- Neutral (pos 8) reserved for aggregates/residuals/reference lines.
- 5 lighter members (lavender, ochre, cyan, lime, amber) fall under WCAG 3:1 on cream bg. Add a 1px ink stroke on affected series when the chart is small or accessibility-strict — see outline pattern in `docs/reference/palette-variants-v3/decision-rationale.md`.
- Non-categorical: sequential → `imprint_seq` (green→blue); diverging → `imprint_div` (red↔theme-adaptive-midpoint↔blue). Never substitute viridis/cividis/BrBG/jet/hsv/rainbow — palette identity is part of the brand.
- Plot-internal typography (ticks/labels/legends): MonoLisa, 10–13px.
