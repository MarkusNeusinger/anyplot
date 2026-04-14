# Frontend Design Guide

The visual language for the **anyplot.ai** website — typography, layout, spacing, and component patterns. This document captures the reasoning behind each design decision so the system stays consistent as the site grows.

The guiding principle throughout: **the website is the neutral frame; the plots are the content.** Every design choice should make room for the data visualizations to do the work.

## TL;DR

Editorial-scientific aesthetic: warm off-white backgrounds, a mix of serif display type and monospaced details, generous whitespace, minimal chrome. The brand color `#009E73` appears only in small, deliberate moments — logo dot, italic accents in headlines, hover states, active navigation. Everything else is grayscale, so when a chart appears, its colors land with full impact.

Think `arXiv paper` × `developer tool` rather than `SaaS dashboard` or `AI startup`.

## Design principles

### 1. Reserve color for moments that earn it

The Okabe-Ito palette has seven saturated colors. If the website itself uses them liberally — brightly colored buttons, banners, hero backgrounds — the actual plots lose their visual punch. We treat the palette as **precious**: the brand green appears in maybe five to ten places on a given page (logo, one italic headline accent, primary CTA hover, active nav indicator, a handful of link underlines). Everything else is one of the seven gray tones.

When a plot appears, it brings new color into a predominantly neutral layout. That contrast is what makes the visualizations feel important.

### 2. Warmth over clinical

Pure `#FFFFFF` backgrounds make the palette colors look harsh and the whole layout feel like a banking app. We use a warm off-white (`#F5F3EC`) as the base, with slightly lighter surfaces (`#FAF8F1`) for cards. This gives the page a paper-like quality that complements the scientific framing — and importantly, it makes the saturated plot colors look **intentional** rather than loud.

Dark mode mirrors this: `#121210` rather than pure black, with a subtle warm undertone.

### 3. Typography carries the editorial weight

Instead of using one font everywhere (standard SaaS move), we pair three with distinct roles:

- **Serif (Fraunces)** for display type, headlines, long-form prose
- **Sans-serif (Inter)** for UI elements, small metadata
- **Monospace (MonoLisa)** for code, logo, technical labels

The serif communicates "considered, readable, editorial." Fraunces specifically was chosen because it has a proper italic (not just a slanted roman) and a characterful drawing that looks modern without being trendy. When we set `"one"` in italic green inside a headline, the italic has real presence — it's a design moment, not a default.

### 4. Generous vertical rhythm

Section padding is 80px vertical on desktop. Hero sections get 80–100px. Cards have 24–28px internal padding. This is significantly more breathing room than most modern sites, and it's deliberate: the layout should feel **unhurried**, like a journal you read cover to cover rather than a dashboard you scan.

### 5. Details reward attention

Small touches that reward a user who looks closely:

- The logo dot pulses subtly in the hero-plot legend
- Active navigation items have a small green dot prefix (matches the logo)
- The palette strip at the bottom expands the hovered color and contracts the rest
- Code blocks have the `● ● ●` macOS-style header dots, rendered in 10% opacity
- Hero headline animates in with staggered reveals (serial rise)

None of these are essential to function. They're there because someone, somewhere, will notice, and they signal "this was made with care."

## Layout system

### Grid and container

- **Max content width**: 1240px (narrower than most modern sites — keeps line lengths comfortable for the serif body text)
- **Gutter**: 24px on mobile, scaling to 96px on wide screens
- **Hero grid**: 1.1fr / 1fr (left content, right plot) — slight bias to the left because headlines need room
- **Library grid**: `auto-fill, minmax(280px, 1fr)` — responsive without breakpoint hell

### Section structure

Each section follows a consistent three-part header:

```
┌──────────────┬──────────────────────┬──────────┐
│ § 01         │   Section title      │  link →  │
└──────────────┴──────────────────────┴──────────┘
```

Left: paragraph number in mono type (editorial convention)
Center: section title in Fraunces, usually with an italic green accent word
Right: optional link in mono, right-aligned

The separator is a 1px bottom border in `--rule` color. Consistent across all sections.

### Masthead rule

The site opens with a thin horizontal rule displaying:

```
Vol. 1 · Spring 2026 │ anyplot.ai — a catalogue of scientific plotting │ Toggle Theme
```

This is a tiny but high-impact element. It immediately positions the site as a curated publication, not a software product page. Costs almost nothing, communicates a lot.

## Typography scale

### Fonts

```css
--serif: 'Fraunces', Georgia, serif;
--sans:  'Inter', system-ui, sans-serif;
--mono:  'MonoLisa', 'JetBrains Mono', 'Fira Code', monospace;
```

Fraunces requires loading from Google Fonts. MonoLisa requires a license (self-hosted); falls back cleanly to JetBrains Mono which is free and visually similar.

### Roles

| Element           | Font    | Size               | Weight | Notes                          |
|-------------------|---------|--------------------|--------|--------------------------------|
| Display headlines | serif   | `clamp(48, 7vw, 96px)` | 400    | With italic green accent word  |
| Section titles    | serif   | `clamp(36, 4.5vw, 56px)` | 400  | Italic green on key word       |
| Body lede         | serif   | 20px               | 300    | Light weight, warm reading     |
| Body paragraph    | sans    | 16px               | 400    | Where long text is unavoidable |
| Eyebrow / Kicker  | mono    | 11px               | 500    | Uppercase, tracked `.15em`     |
| UI labels         | mono    | 12–13px            | 500    |                                |
| Code / logo       | mono    | context-dependent  | 700    | Logo uses the `any.plot()` syntax |
| Stats / numerals  | serif   | 56px               | 300    | Italic accent on key digit     |

The key rule: **serifs for reading, mono for metadata, sans only when the sans provides something (like multi-weight support) that the others can't.** In practice Inter shows up rarely — most body text is serif because the site leans editorial.

### Display type details

The hero headline uses a specific construction:

```
Any library,
[italic green]one[/italic] any.plot()
```

Where `any.plot()` is rendered in mono-bold at 0.75× the headline size, with the `.` styled in green and scaled up. The effect is a headline that is half-typographic, half-code — consistent with the brand identity.

## Color application in UI

### The brand color rules

`#009E73` (brand green) appears in the UI only in these contexts:

1. Logo dot (always)
2. Italic accent words in headlines
3. Active navigation item (green dot prefix + underline on hover)
4. Primary button hover state (CTA text button → green background on hover)
5. Code block syntax highlighting (strings, specific tokens)
6. Palette strip and any deliberate palette display
7. Small status indicators (pulsing dot in plot-card header)

It does **not** appear in:

- Background colors (never)
- Borders of regular cards (use `--rule` = `rgba(26,26,23,0.10)`)
- Body text emphasis (use serif italic instead)
- Icon colors outside of logos (use gray tones)

### Grayscale

We use a warm-tinted grayscale rather than neutral:

| Token         | Light         | Dark          | Role                       |
|---------------|---------------|---------------|----------------------------|
| `--ink`       | `#1A1A17`     | `#F0EFE8`     | Primary text               |
| `--ink-soft`  | `#4A4A44`     | `#B8B7B0`     | Secondary text             |
| `--ink-muted` | `#8A8A82`     | `#6E6D66`     | Tertiary, meta, labels     |
| `--rule`      | `rgba(26,26,23,0.10)` | `rgba(240,239,232,0.10)` | Borders, dividers |

The warm bias (reddish-brown undertone instead of blue-gray) matches the paper-like background and avoids the "tech blue" feel.

### Other Okabe-Ito colors in UI

The remaining palette colors have reserved UI roles:

- `#D55E00` (Vermillion) — destructive actions, error states
- `#E69F00` (Orange) — "new" badges, hover highlights on secondary elements
- `#0072B2` (Blue) — informational links in prose, footnotes

Purple, Sky, and Yellow are **plot-only** and do not appear in the UI at all. This preserves their visual impact for the data visualizations.

## Components

### Plot card

The fundamental display unit for any visualization:

```css
background: var(--bg-surface);
border: 1px solid var(--rule);
border-radius: 12px;
padding: 28px;
box-shadow: 0 1px 2px rgba(0,0,0,0.02),
            0 24px 48px -24px rgba(0,0,0,0.08);
```

Two-layer shadow: the first (`0 1px 2px`) gives a sharp edge that keeps the card visually anchored; the second (`0 24px 48px -24px`) is a soft ambient drop that suggests elevation without being heavy. This combination reads as "considered" rather than "generic card-ified."

The card has three vertical zones:

```
┌──────────────────────────────────────┐
│ header: mono code title   meta ↗    │  12–14px bottom margin
├──────────────────────────────────────┤
│                                      │
│   [ plot SVG area ]                  │
│                                      │
├── dashed rule ──────────────────────┤
│ footer: legend items   caption →    │  12–16px top padding
└──────────────────────────────────────┘
```

The dashed rule between plot and legend is a subtle but important detail — it differentiates the legend from the plot without drawing attention. Solid rules feel too structural for this role.

### Library card

Used in the catalogue grid. Similar to plot card but with specific additions:

- Top 2px accent bar, initially `scaleX(0)`, animates to `scaleX(1)` on hover (color varies per library via `--accent` custom property)
- Hover lifts card by 3px (`translateY`) and softens border toward brand green
- Mini-plot thumbnail uses SVG at fixed 120px height
- Library name in mono-bold, example count in mono-muted

The color of the accent bar is a subtle way to give each library a personality without breaking the shared palette system — every library gets one of the Okabe-Ito colors as its accent.

### Buttons

Two variants only:

**Primary (CTA)**

```css
background: var(--ink);
color: var(--bg-page);
border-radius: 99px;   /* pill shape */
padding: 13px 22px;

/* on hover */
background: var(--ok-green);
color: #FFF;
```

The dark-to-green transition on hover is a signature moment. The button is always darker than its container at rest (maximum contrast, clear affordance), then shifts to brand green on interaction (confirming the action as "on brand").

**Ghost (secondary)**

```css
background: transparent;
color: var(--ink);
border: 1px solid var(--rule);
```

Used for secondary actions where the primary already occupies visual space. Border darkens on hover without filling.

### Code block

Dark block, even in light mode. The reasoning: code is "different material" — like a photograph inside a magazine. Forcing it to be light-on-light would make it blend into the surrounding text and lose its "this is code" signal.

```css
background: #0E0E0C;
color: #E8E8E0;
border-radius: 12px;
padding: 28px 32px;
font: 14px/1.7 var(--mono);
box-shadow: 0 24px 48px -16px rgba(0,0,0,0.2);
```

The fake macOS window-controls (`● ● ●` in 10% opacity) are rendered via a `::before` pseudo-element at the top-left. Playful but not distracting. They also subtly communicate "this is a screenshot of real code running somewhere" which fits the developer-tool framing.

Syntax highlighting uses the Okabe-Ito palette:

- Keywords → sky blue
- Strings → brand green
- Function names → orange
- Comments → gray (`#666`, italic)
- Variables → purple
- Numbers → yellow (rare, because the cold Yellow works fine on dark bg)

### Navigation

Horizontal text links, no icons, no boxes. On hover, a 1px green underline animates in from the left (`transform-origin: left; transform: scaleX(0) → scaleX(1)`). On active state, a small green bullet (`•`) appears 12px to the left of the text.

```css
.nav a::after {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 1px;
  background: var(--ok-green);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.nav a:hover::after { transform: scaleX(1); }
```

The `cubic-bezier(0.4, 0, 0.2, 1)` is the standard material-motion "ease-in-out" curve — smooth but with enough snap to feel crisp.

### Search affordance

Top-right of the nav, styled as a pill with `⌕ search plots` text and a `⌘ K` keyboard hint badge. Button-like but not a solid button — borderless until hover. Clicking would open a command palette (not implemented in the mockup but planned for the real site).

## Animation

Restrained. Three categories only:

### 1. Page load

Hero elements rise from 8px below with opacity transition:

```css
@keyframes rise {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

Staggered via `animation-delay`:

- Eyebrow: 0s
- Headline: 0.1s
- Lede: 0.2s
- CTAs: 0.3s
- Meta: 0.4s
- Hero plot: 0.3s (parallel to CTAs)

Total sequence: ~0.8s. Enough to feel intentional, short enough not to delay interaction.

### 2. Hover states

All transitions use 0.15–0.3s with `cubic-bezier(0.4, 0, 0.2, 1)`. Never use default `ease` — it's too linear for modern motion.

### 3. Palette strip interaction

The palette strip at the bottom responds to hover: normal state is even distribution, `:hover .sw` shrinks all colors to 50%, then `.sw:hover` expands the specific hovered color to 300%. It's a playful detail that invites interaction without being necessary.

```css
.palette-strip .sw { flex: 1; transition: flex 0.3s; }
.palette-strip:hover .sw { flex: 0.5; }
.palette-strip .sw:hover { flex: 3; }
```

## What to avoid

Specific anti-patterns that would break the aesthetic:

- **Gradients**: especially purple-to-blue SaaS gradients. The palette is categorical; continuous gradients would undermine its logic.
- **Glass morphism / backdrop-blur**: too trendy, breaks the paper metaphor.
- **Tech-startup illustrations**: isometric figures, 3D renders, hand-drawn doodles — all wrong register.
- **Parallax effects or hero videos**: too heavy for a content-first site. Layout should feel instantly complete.
- **Badge-heavy UI**: "NEW!" badges, notification dots, progress indicators competing for attention. Reserve attention for plots.
- **Purple** (`#CC79A7`), **Sky** (`#56B4E9`), or **Yellow** (`#F0E442`) in UI chrome. These are plot-only colors. Using them in navigation or buttons breaks the color hierarchy.
- **Pure white or pure black backgrounds**: harsh, removes the warmth, makes plots look awkward against them.
- **Fonts beyond the three chosen**: no Space Grotesk, no Poppins, no Inter Tight, no experiments with IBM Plex Serif. Three fonts is the system.

## Reference points

Aesthetic directions we drew from:

- **observablehq.com** — scientific, plot-centered, monospace details
- **arXiv preprints** — the "considered paper" feel we're targeting
- **Wes Anderson film posters** — for the principle of warm neutrals with knapp, gesättigte Farbakzenten
- **The New York Times' interactive features** — for the editorial layout rhythm
- **Vercel's documentation** — for the clean monospace-heavy technical pages

What we explicitly didn't borrow from:

- Generic SaaS landing pages (Stripe, Linear, Notion)
- AI startup aesthetics (Anthropic site, OpenAI site, HuggingFace)
- Tech-product marketing pages (Vercel's homepage, specifically — too dense with features)

## Implementation file

The reference implementation is a single HTML file, self-contained (no external JS), using CSS custom properties for theming:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>anyplot.ai — any library. one plot.</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      /* Okabe-Ito palette — full 7 + adaptive neutral */
      --ok-green:      #009E73;
      --ok-vermillion: #D55E00;
      --ok-blue:       #0072B2;
      --ok-purple:     #CC79A7;
      --ok-orange:     #E69F00;
      --ok-sky:        #56B4E9;
      --ok-yellow:     #F0E442;

      /* Surfaces — warm off-white, not pure #fff */
      --bg-page:     #F5F3EC;
      --bg-surface:  #FAF8F1;
      --bg-elevated: #FFFDF6;

      /* Warm-tinted grays */
      --ink:         #1A1A17;
      --ink-soft:    #4A4A44;
      --ink-muted:   #8A8A82;
      --rule:        rgba(26, 26, 23, 0.10);

      /* Typography roles */
      --serif: 'Fraunces', Georgia, serif;
      --sans:  'Inter', system-ui, sans-serif;
      --mono:  'MonoLisa', 'JetBrains Mono', 'Fira Code', monospace;

      /* Layout */
      --gutter: 24px;
      --max: 1240px;
    }

    /* Dark theme — toggled by .theme-dark on <body> */
    .theme-dark {
      --bg-page:     #121210;
      --bg-surface:  #1A1A17;
      --bg-elevated: #242420;
      --ink:         #F0EFE8;
      --ink-soft:    #B8B7B0;
      --ink-muted:   #6E6D66;
      --rule:        rgba(240, 239, 232, 0.10);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--sans);
      background: var(--bg-page);
      color: var(--ink);
      font-size: 16px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      transition: background 0.3s, color 0.3s;
    }

    /* === Logo === */
    .logo {
      font-family: var(--mono);
      font-weight: 700;
      font-size: 22px;
      letter-spacing: -0.02em;
    }
    .logo .dot {
      color: var(--ok-green);
      display: inline-block;
      transform: scale(1.45);
      margin: 0 2px;
    }
    .logo .parens { font-weight: 400; opacity: 0.45; }

    /* === Display headline === */
    h1.display {
      font-family: var(--serif);
      font-weight: 400;
      font-size: clamp(48px, 7vw, 96px);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }
    h1.display em {
      font-style: italic;
      font-weight: 300;
      color: var(--ok-green);
    }

    /* === Plot card === */
    .plot-card {
      background: var(--bg-surface);
      border: 1px solid var(--rule);
      border-radius: 12px;
      padding: 28px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.02),
                  0 24px 48px -24px rgba(0,0,0,0.08);
    }

    /* === Primary button === */
    .btn-primary {
      background: var(--ink);
      color: var(--bg-page);
      font-family: var(--mono);
      font-size: 13px;
      padding: 13px 22px;
      border-radius: 99px;
      border: 1px solid transparent;
      transition: all 0.2s;
    }
    .btn-primary:hover {
      background: var(--ok-green);
      color: #FFF;
    }

    /* === Nav hover underline === */
    .nav a { position: relative; }
    .nav a::after {
      content: '';
      position: absolute; bottom: 0; left: 0; right: 0;
      height: 1px;
      background: var(--ok-green);
      transform: scaleX(0);
      transform-origin: left;
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .nav a:hover::after { transform: scaleX(1); }

    /* === Page-load animation === */
    @keyframes rise {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .hero > * { animation: rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) backwards; }
  </style>
</head>
<body>
  <!-- Content goes here. See full reference file for complete markup. -->
</body>
</html>
```

The full reference file (with all sections, SVG plots, and animations) lives in `mockups/landing.html`.

## Fonts and licensing

- **Fraunces**: free, Open Font License. Load via Google Fonts CDN.
- **Inter**: free, Open Font License. Load via Google Fonts CDN or self-host.
- **JetBrains Mono**: free, Open Font License. Fallback for MonoLisa.
- **MonoLisa**: commercial license required. Self-hosted with `@font-face` rules. Licensed per developer — check the license terms before deploying to production. The site should function gracefully if MonoLisa isn't loaded (fallback chain handles this).

---

*Last updated: 2026. This is a living document. Update it whenever a design pattern is established or refined.*