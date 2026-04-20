# Style Guide

```
❯ anyplot.ai — design system
─────────────────────────────
brand · frontend · plots — one reference for every adjustment
```

The complete design system for **anyplot.ai** — brand identity, frontend visual language, and plot color system in one document. Use this for any frontend adjustment, content tone decision, or plot styling choice.

The guiding principle throughout: **the website is the neutral frame; the plots are the content.** Every design choice should make room for the data visualizations to do the work — and every interaction should feel native to someone who lives in a terminal or code editor.

---

## 1. TL;DR

anyplot.ai is a considered reference work styled like a code editor over a paper magazine. Three layers, each with a clear role:

| Layer | Role | Anchor |
|-------|------|--------|
| **Brand** | Identity, voice, logo, tone of communication | Lowercase default; `any.plot()` wordmark with green dot |
| **Frontend** | Website visual language: typography, layout, components | Editorial-scientific paper × terminal/code-editor overlay |
| **Plots** | Color palette for every visualization across all 9 libraries | Okabe-Ito 8-color categorical, brand `#009E73` first |

**Aesthetic direction:** `arXiv paper` × `tmux/lazygit` rather than `SaaS dashboard` or `AI startup`. The reader should feel they're browsing a curated journal that happens to live inside a terminal — section headers carry shell prompts (`❯`, `$`, `~/plots/`), hero text types itself with a blinking cursor, action buttons read as method calls (`.copy()`, `.open()`, `.download()`).

**Color discipline:** `#009E73` (Okabe-Ito Bluish Green) appears only in small, deliberate moments — logo dot, italic accents, hover states, active navigation, terminal cursor. Everything else is warm grayscale, so when a chart appears its colors land with full impact.

**Pipeline transparency:** AI is part of the story, not a hidden production detail. Humans submit ideas (plot requests as GitHub issues); AI drafts the spec from the idea; humans approve the spec before any code runs; AI generates the implementations and reviews them; on rejection AI retries and humans tune the rules or refine the spec. Communicated openly in copy and methodology pages.

---

## 2. Design Principles

### 2.1 Visual principles (frontend)

**1. Reserve color for moments that earn it.** The Okabe-Ito palette has seven saturated colors. If the website itself uses them liberally — brightly colored buttons, banners, hero backgrounds — the actual plots lose their visual punch. We treat the palette as **precious**: the brand green appears in maybe five to ten places on a given page (logo, one italic headline accent, terminal cursor, primary CTA hover, active nav indicator, a handful of link underlines). Everything else is one of the seven gray tones.

**2. Warmth over clinical.** Pure `#FFFFFF` backgrounds make palette colors look harsh and the layout feel like a banking app. We use a warm off-white (`#F5F3EC`) as the base, with slightly lighter surfaces (`#FAF8F1`) for cards. This gives the page a paper-like quality and makes the saturated plot colors look **intentional** rather than loud. Dark mode mirrors this: `#121210` rather than pure black, with a subtle warm undertone.

**3. Code is the native register.** Section headers carry shell prompts (`❯ libraries`, `$ plots`, `~/anyplot/`), action buttons read as method calls (`.copy()`, `.open()`, `.download()`), the hero headline types itself with a blinking cursor. The site speaks the dialect of its visitors. This is not skinning — it's the framing device. Removing the editorial paper underneath would over-tip into "developer toy"; removing the terminal layer would feel sterile and product-marketing-y. The two layers depend on each other.

**4. One typeface, two voices.** The entire site is set in **MonoLisa** — body, UI, navigation, prompts, buttons, logo, display headlines, everything. The editorial accent is not a second font but MonoLisa's **italic + `ss02` stylistic set** (the script variant), enabled globally via `font-feature-settings: "ss02"`. Whenever text is set in `font-style: italic`, it renders as a flowing script that carries the emotional/editorial register while staying on the monospace grid.

- **Roman (upright MonoLisa)** — default for all prose, labels, navigation, buttons, code, logo. Bold weights (700) for display sizes.
- **Script (italic MonoLisa + ss02)** — accents only: hero sub-headlines (`— any library.`), section titles (`libraries`, `specs`), taglines (`steal like an artist.`), emphasized words (`<em>your</em>`). Reserve for semantic emphasis, not decoration.

This is a stricter system than the typical 3-font stack and depends on MonoLisa's breadth (all weights 100–900, italic with ss02) rather than bringing in a separate serif. The trade-off: no Fraunces editorial warmth; in exchange, a single coherent voice.

**5. Generous vertical rhythm.** Section padding is 80px vertical on desktop. Hero sections get 80–100px. Cards have 24–28px internal padding. The layout should feel **unhurried**, like a journal you read cover to cover rather than a dashboard you scan.

**6. Self-evident, not explained.** Buttons should not need labels saying "click here to copy" — they say `.copy()` and that is enough. Icons may exist but are secondary; the primary affordance is text in mono that reads like code. If a coder would understand `df.head()` without help, they will understand `.preview()` on a plot card. Explanation prose belongs in docs, not on the page chrome.

**7. Details reward attention.** Small touches that reward a user who looks closely: the cursor blinks in the hero, the logo dot pulses subtly in the hero-plot legend, active navigation items have a small green dot prefix, the palette strip at the bottom expands the hovered color and contracts the rest, code blocks have `● ● ●` macOS-style header dots in 10% opacity, the side plot stacks scroll lazily on ultrawide. None essential to function — they signal "this was made with care."

### 2.2 Verbal principles (voice)

The brand voice is:

1. **Precise** — we say exactly what we mean, with the right technical terminology
2. **Understated** — we let the work speak; we don't overhype
3. **Curious** — we share interesting details and reasoning, not just conclusions
4. **Respectful of the reader** — we assume technical literacy without being condescending
5. **Slightly playful** — the occasional small joke, mostly structural (the method-call logo, the `import anyplot as ap` alias, comments-as-prose)
6. **Code-native** — when in doubt, write it as code. Pipelines as arrows (`spec → code → review`), state as flags, errors as stderr lines. Prose only where prose actually helps.
7. **AI-honest** — AI generates the code and runs the reviews. We say so plainly. We don't hype it ("AI-powered"), and we don't hide it ("magically generated").

Tone attributes we avoid:
- **Sales-y** — no "unlock", "supercharge", "revolutionary", "game-changing"
- **Corporate** — no "solutions", "leverage", "empower", "synergies"
- **Breathless** — no excessive exclamation marks, no "literally" or "amazing"
- **AI-hype** — no "powered by AI", "intelligent", "smart" — but we *do* describe what the AI actually does
- **Emoji-heavy** — avoid emojis in documentation and formal writing

---

## 3. Brand Identity

### 3.1 Name & Pronunciation

**anyplot.ai** carries three ideas:

- **"any"** — library-agnostic. Not "py" because the project's long-term vision extends beyond one language.
- **"plot"** — the core object. We're not abstracting away the plot; we're cataloguing it.
- **".ai"** — the modern TLD, inherited from `pyplots.ai`. Signals "contemporary technical project" without claiming AI-generated content.

**Pronunciation:** "any-plot dot AI" — three distinct words, not "any-plottie". The dot is pronounced because the domain structure matters.

Alternative casual forms:
- "anyplot" (when domain isn't needed)
- "ap" (in code: `import anyplot as ap`)

**Relationship to pyplots.ai:** `pyplots.ai` is the predecessor. The rebrand is communicated as evolution, not replacement: "anyplot.ai is the next chapter of pyplots.ai — broader in scope (beyond Python), broader in language (beyond English), and anchored in a colorblind-safe palette that travels across every library."

### 3.2 Logo

The logo is typographic, rendered in MonoLisa Bold:

```
any.plot()
```

Specifically:

- `any` in `--ink` (near-black on light, near-white on dark)
- `.` in `--ok-green` (`#009E73`), scaled to 145% with 2–3px horizontal margin
- `plot` in `--ink`
- `()` in `--ink` at 45% opacity, normal weight (not bold)

The `.` is the single most important brand element. It is:

- The method-call operator, signaling "this is code"
- A data point, the atomic unit of a plot
- The color anchor (the one place brand green always appears)

All three readings are intentional.

**Geometry:**

```
letter-spacing: -0.02em  (slight negative tracking for density)
font-weight:    700 (bold) for letters, 400 (regular) for parens
```

**Sizes:**

| Context           | Size       | Notes                           |
|-------------------|-----------|---------------------------------|
| Favicon / app icon| 16–64px   | Reduce to `a.p` — keeps the dot |
| Top-nav           | 18–22px   | Standard use                    |
| Hero section      | 40–64px   | Occasional, paired with headline|
| Large display     | 80–96px+  | Landing hero, posters           |

**Color variants:**

- **On light background**: ink-dark letters, green dot — default
- **On dark background**: ink-light letters, green dot stays the same
- **On brand green background**: do not use — too little contrast. Use monochrome white version instead.
- **Monochrome**: all letters in `--ink`, dot also in `--ink`. Used in print, fax-friendly contexts, and the occasional t-shirt.

**What the logo is not:** not an illustration, icon, or mascot. We don't have a plot-graph silhouette, a Python-snake variant, or an anthropomorphic data point. The typographic wordmark is the entire brand mark. Resist the urge to add visual flourishes.

**Clear space:** maintain at least `1em` (one letter-height) around the wordmark on all sides. Inside the clear space, no other text, graphics, or UI elements may appear.

### 3.3 Taglines

**Canonical hero block:**

```
any.plot() — any library.

get inspired.
grab the code.
make it yours.
```

The first line (`any.plot() — any library.`) is the wordmark + product proposition in one breath. The three lines below are the user journey, in the imperative, in lowercase, each one standalone. Together they describe exactly what the site is for: discovery → copy → adaptation. Use this hero block on:

- Landing page hero (full block, with terminal box framing and blinking cursor on the last line)
- Meta description (compress to: `any library. get inspired. grab the code. make it yours.`)
- README headline (full block, in a code fence)
- OG card (line 1 in serif, lines 3–5 in mono)

**Short forms:**

- **"any library."** — when only one phrase fits (browser tab title suffix, social bio one-liner)
- **"get inspired. grab the code. make it yours."** — when the wordmark is already shown nearby (e.g., footer subtitle below the logo)

**Alternative taglines for specific contexts:**

- **"a catalogue of scientific plotting"** — editorial framing, when contextualizing the project in academic writing
- **"from anyplot import *"** — code-playful, good for dev-audience posts
- **"plots that everyone can see"** — accessibility-focused, good for technical articles about colorblind safety
- **"human ideas. ai builds the rest."** — methodology framing, for about/methodology pages

Rotate alternatives as appropriate. The canonical hero block is always the first choice.

**Taglines we explicitly don't use:**

- "the future of data visualization" (overclaim)
- "AI-powered plotting catalogue" (lazy AI-hype framing — say what the AI does, don't sloganize it)
- "plot anything, anywhere, anytime" (cliché, generic)
- "the GitHub of plots" (imitative framing)

### 3.4 Voice & Tone

See §2.2 for the five tone attributes (precise, understated, curious, respectful, slightly playful) and what to avoid.

### 3.5 Capitalization & Punctuation

**Default: lowercase.** UI labels, section titles, taglines, button text — all lowercase unless there's a specific reason.

Reasons to use uppercase:

- Proper nouns (library names like `matplotlib` are lowercase because that's how they're written; `GitHub` is uppercase because that's how it's written — follow upstream conventions)
- First word of a sentence in long-form prose
- Proper names of people or places
- Code identifiers that are uppercase in their original context

The lowercase default matches the code-forward aesthetic and keeps the site feeling quiet.

**Punctuation:**

- **Oxford comma**: yes, always (we write for a technical audience that tends to appreciate grammatical clarity)
- **Em-dashes**: used freely for parenthetical asides — like this — with spaces around them (European style)
- **Sentence structure**: prefer short, declarative sentences. Longer sentences are fine when the content demands it.
- **Questions**: rare. We usually state things rather than ask them.

### 3.6 Voice Examples (do / don't)

**Announcing a new library:**

> Do: `plotnine support just landed. 74 new examples using the grammar of graphics.`
>
> Don't: `🎉 Big news! We're excited to announce that plotnine is now fully supported on anyplot.ai! Check out our awesome new collection of 74 examples! 🚀`

**Error message:**

> Do:
> ```
> $ ap.load("ggplot")
> ✗ unknown library: "ggplot"
>   supported: matplotlib, seaborn, plotly, bokeh,
>              altair, plotnine, pygal, highcharts, lets-plot
> ```
>
> Don't: `Oops! Looks like we don't support "ggplot" yet. But don't worry — we're always adding new libraries! 🙂`

**Changelog entry:**

> Do:
> ```
> v0.4.0
> + altair support
> + palette exports accept theme="light"|"dark"
> ~ seaborn examples now include legends (was: omitted)
> ```
>
> Don't: `🎉 v0.4.0 is here! We've been working hard to bring you some amazing new features...`

**GitHub issue response to a feature request:**

> Do: `interesting idea. doesn't fit the catalogue scope right now — anyplot is static examples, this needs interactive features. keeping open for discussion.`
>
> Don't: `Thanks so much for this amazing feature request!! ❤️ We'll definitely consider this for our roadmap!`

**Describing the AI pipeline:**

> Do:
> ```
> // pipeline
> idea    → human-submitted        (github issue)
> spec    → ai-drafted, human-approved
> code    → ai-generated           (per library)
> review  → ai-evaluated
> fix     → ai-retries; humans tune rules
> ```
>
> Don't: `Powered by cutting-edge AI to bring you the best plotting examples!`
>
> Don't: `Specs hand-crafted by experts.` — they aren't; they're AI-drafted from a human one-liner, then human-approved.

**The pattern:** state the mechanism, name what does what, no breathless framing. When in doubt, format as code — pipelines as arrows, results as `+`/`~`/`-`/`✗`.

**Long-form transformation example:**

> Instead of: `🚀 Supercharge your data viz workflow with AI-powered plot generation! Unlock 1000+ beautifully crafted charts across multiple libraries. Ship faster, iterate smarter, and empower your team to create stunning visualizations!`
>
> Write: `A catalogue of 1,000+ plotting examples across nine Python libraries. Plot ideas come from humans; AI drafts the spec, generates code for every library, and reviews each implementation. Humans approve specs and tune the rules when something repeatedly fails. Every example uses the same colorblind-safe palette, so switching libraries never breaks your color grammar.`

The second version is shorter, says what's actually happening (humans submit ideas + approve + tune; AI does the drafting/generating/reviewing), and reads as if written by someone who cares about what they're building.

### 3.7 Positioning

**What anyplot is:**

- A **reference catalogue**, like a cookbook or an atlas. You come for specific examples.
- **Library-agnostic**, showing the same chart types across matplotlib, seaborn, plotly, and others.
- **Colorblind-safe by default**. Every example uses the Okabe-Ito palette. This isn't a feature, it's a baseline.
- **Copyable**. Every example is self-contained, with the full code visible and executable.
- **Curated**. We don't aggregate every plot on the internet — we maintain a considered collection.
- **AI-built, human-shaped.** Plot ideas come from humans (GitHub issues). Everything else — drafting the spec, generating code per library, reviewing it — runs on AI. Humans approve specs before any code is generated, and when something repeatedly fails review we either refine the spec or tune the AI rules. We never patch generated code by hand. The pipeline is documented and visible.

**What anyplot is not:**

- **A plotting library**. We don't compete with matplotlib or plotly. We help you use them better.
- **An AI plot generator the user prompts.** Users browse a curated catalogue. They don't type prompts; the AI runs offline against specs.
- **A dashboard tool**. We show static examples. Interactive dashboards are a different product category.
- **A tutorial platform**. We assume you know how to run Python code. We don't teach from zero.
- **A community forum**. We accept contributions through GitHub but we're not building a social layer.

### 3.8 Story Points

Narrative hooks for talking about anyplot — adapt to context, don't recite verbatim:

**The pipeline story:** Humans submit plot ideas as GitHub issues. AI drafts the spec from each idea; humans approve it before any code is generated. AI then generates implementations for all nine libraries from the same spec and reviews each one for visual quality and spec compliance. When something doesn't pass review, AI retries — and when it keeps failing, we refine the spec or tune the AI rules. We never patch the code by hand. That makes anyplot a catalogue that maintains itself: when matplotlib ships a new release, we re-run the pipeline; when a better example pattern emerges, we update the spec and every library regenerates. Humans curate; AI executes.

**The palette story:** Every plot uses the Okabe-Ito palette, peer-reviewed for colorblind safety and designed for scientific publications in 2008. About 8% of men have some form of color vision deficiency — most plotting libraries ignore this entirely. We make it the default.

**The library-agnostic story:** A "Gentoo penguin" is always blue, whether you draw it in matplotlib, plotly, or bokeh. The palette travels with you across libraries. Switching tools doesn't mean re-learning your color grammar.

**The catalogue story:** A thousand examples across nine libraries, each reproducible and copy-pasteable. No ads. No affiliate links. No "suggested tutorials you might like." Just the plots and the code that made them.

**The origin story:** It started as pyplots.ai, a small Python-only catalogue I built in a weekend. It grew when I realized people wanted the same examples across different libraries, and the same safe palette everywhere. anyplot is the grown-up version.

**The personal touch:** Built in Visp, a small town in the Swiss Alps. By a data analyst who spent too many hours trying to figure out why the same chart looked different in seaborn than in plotly.

### 3.9 Naming Conventions

**Library:**
- **Package name**: `anyplot` (lowercase, one word)
- **Import convention**: `import anyplot as ap`
- **Sub-modules**: `anyplot.mpl`, `anyplot.plotly`, `anyplot.bokeh`, etc. — one sub-module per supported library
- **Palettes**: `anyplot.palettes.okabe_ito`, `anyplot.palettes.viridis`, etc.
- **Datasets**: `anyplot.load("penguins")`, `anyplot.load("iris")` — not `load_penguins()`; consistent loader signature

**Domain:**
- **Primary**: `anyplot.ai`
- **Language redirects**: `python.anyplot.ai` → `anyplot.ai/python/`, etc.
- **Documentation**: `docs.anyplot.ai` (planned)

**Examples and identifiers:**
- A **slug** (URL-safe): `matplotlib-scatter-penguins-species`
- A **title** (human-readable): `Scatter plot of penguin species`
- A **library**: one of the nine supported
- **Tags**: chart type, data domain, complexity level

Slugs are the canonical identifier. They're used in URLs, filenames, and `ap.load()` calls.

---

## 4. Color System

### 4.1 The Okabe-Ito Palette

The Okabe-Ito palette was published in 2008 by Masataka Okabe (Jikei Medical School) and Kei Ito (University of Tokyo) as part of their research on accessible color design for scientific figures. It was optimized empirically for three types of color vision deficiency (CVD) — deuteranopia, protanopia, and tritanopia — which together affect roughly 8% of men and 0.5% of women of Northern European descent.

Three properties make it the right choice for a multi-library plotting catalogue:

**Peer-reviewed and widely trusted.** ggplot2, seaborn, and many scientific R/Python toolkits offer it as a built-in option. Using it means our examples are immediately credible in academic and publication contexts.

**Stable across backgrounds.** Every color has enough luminance contrast to remain distinguishable on both white and near-black backgrounds.

**Eight colors is the right cap.** Research by Ware, Glasbey, and Miller on distinguishable categorical colors converges on 7 ± 2 as the practical limit before viewers start confusing categories.

```python
anyplot_palette = [
    "#009E73",  # 01 · bluish green   ★ brand
    "#D55E00",  # 02 · vermillion
    "#0072B2",  # 03 · blue
    "#CC79A7",  # 04 · reddish purple
    "#E69F00",  # 05 · orange
    "#56B4E9",  # 06 · sky blue
    "#F0E442",  # 07 · yellow
    # 08 · neutral — adaptive: #1A1A1A on light, #E8E8E0 on dark
]
```

**The colors:**

| # | Role          | Hex        | Semantic Use                                                  |
|---|---------------|------------|---------------------------------------------------------------|
| 1 | Brand         | `#009E73`  | Logo dot, first category in any plot, primary CTAs            |
| 2 | Secondary     | `#D55E00`  | Second category, warm contrast, warnings                      |
| 3 | Tertiary      | `#0072B2`  | Third category, cool anchor, informational links              |
| 4 | Quaternary    | `#CC79A7`  | Fourth category, soft, distinctive                            |
| 5 | Accent warm   | `#E69F00`  | Fifth category, highlights, hover states                      |
| 6 | Accent cool   | `#56B4E9`  | Sixth category, info states, secondary links                  |
| 7 | Highlight     | `#F0E442`  | Seventh category — use sparingly, poor on white backgrounds   |
| 8 | Neutral       | adaptive   | Text, gridlines, "other", totals                              |

**The adaptive neutral.** Position 8 is not a fixed color but a **role** that switches based on the theme:

- **Light theme** → `#1A1A1A` (near-black, softer than pure `#000`)
- **Dark theme** → `#E8E8E0` (near-white, softer than pure `#FFF`)

This follows the `semantic tokens` pattern used in Apple HIG, Material Design, and GitHub Primer. The first seven colors stay identical across themes so that a category retains its identity; only the neutral flips.

**Order matters.** The color order is **not scientifically prescribed** — the Okabe-Ito paper lists the colors but doesn't mandate a sequence. We've chosen an order optimized for two goals:

1. **Brand consistency.** Position 1 is always `#009E73`. The first data series in every plot is automatically our brand color.
2. **Maximum early contrast.** Positions 1–4 alternate between warm and cool, saturated hues to guarantee maximum distinguishability for plots with few categories. Orange (`#E69F00`) and Yellow (`#F0E442`) — which share the yellow-orange region — are separated by four positions.

```
green → vermillion → blue → purple → orange → sky → yellow → neutral
warm?   warm         cool    warm     warm      cool   warm    neutral
sat.    sat.         sat.    sat.     sat.      soft   soft
```

### 4.2 Surfaces

Plots and content sit inside **surface containers** with consistent styling:

| Surface     | Light          | Dark           | Use                         |
|-------------|----------------|----------------|-----------------------------|
| `bg-page`   | `#F5F3EC`      | `#121210`      | Outer page background       |
| `bg-surface`| `#FAF8F1`      | `#1A1A17`      | Cards, plot containers      |
| `bg-elevated`| `#FFFDF6`     | `#242420`      | Modals, tooltips            |

The warm off-white (`#F5F3EC`) is the foundation — pure white would make the saturated palette colors look harsh.

### 4.3 Warm-tinted Grayscale

A warm-tinted grayscale (reddish-brown undertone instead of blue-gray) matches the paper-like background and avoids the "tech blue" feel.

| Token         | Light                       | Dark                          | Role                       |
|---------------|-----------------------------|-------------------------------|----------------------------|
| `--ink`       | `#1A1A17`                   | `#F0EFE8`                     | Primary text               |
| `--ink-soft`  | `#4A4A44`                   | `#B8B7B0`                     | Secondary text             |
| `--ink-muted` | `#8A8A82`                   | `#6E6D66`                     | Tertiary, meta, labels     |
| `--rule`      | `rgba(26,26,23,0.10)`       | `rgba(240,239,232,0.10)`      | Borders, dividers          |

### 4.4 UI Color Application

`#009E73` (brand green) appears in the UI **only** in these contexts:

1. Logo dot (always)
2. Italic accent words in headlines (e.g., `any library.`)
3. Hero terminal cursor (the blinking `▌` at the end of `make it yours._`)
4. Active navigation item (green dot prefix + underline on hover)
5. Code-style action button hover (`.copy()` → green on hover) and CTA hover (filled background swap)
6. Code block syntax highlighting (strings, specific tokens)
7. Palette strip and any deliberate palette display
8. Small status indicators (pulsing dot in plot-card header)

It does **not** appear in:

- Background colors (never)
- Borders of regular cards (use `--rule` = `rgba(26,26,23,0.10)`)
- Body text emphasis (use serif italic instead)
- Icon colors outside of logos (use gray tones)
- Static (non-cursor, non-status) decorative dots or glyphs

### 4.5 Status Colors

The remaining Okabe-Ito palette colors have reserved UI roles:

- `#D55E00` (Vermillion) — destructive actions, error states
- `#E69F00` (Orange) — "new" badges, hover highlights on secondary elements
- `#0072B2` (Blue) — informational links in prose, footnotes

### 4.6 Plot-only Colors

**Purple (`#CC79A7`), Sky (`#56B4E9`), and Yellow (`#F0E442`) are plot-only and do not appear in the UI at all.** This preserves their visual impact for the data visualizations.

Using them in navigation or buttons breaks the color hierarchy.

---

## 5. Typography

### 5.1 Font Families

```css
--serif: 'MonoLisa', 'MonoLisa Fallback', Consolas, Menlo, Monaco, 'DejaVu Sans Mono', monospace;
--sans:  'MonoLisa', 'MonoLisa Fallback', Consolas, Menlo, Monaco, 'DejaVu Sans Mono', monospace;
--mono:  'MonoLisa', 'MonoLisa Fallback', 'JetBrains Mono', Consolas, monospace;
```

The `--serif` and `--sans` variables are kept as aliases to `--mono` so existing imports resolve, but all three resolve to the same MonoLisa stack. The editorial accent comes from **italic + `ss02` stylistic set**, not from a second font. `ss02` is enabled globally on `html` via `font-feature-settings: "ss02"` — it only affects glyphs rendered with `font-style: italic`, so upright text is unaffected.

**Loading:**
- **MonoLisa 2.017**: commercial license required. Self-hosted on GCS (`gs://anyplot-static/fonts/`) as 64 Unicode-range subsets (woff2, variable 100–900 weights, normal + italic). The italic subsets ship with the `ss02` feature table intact — critical for the script variant. CORS restricted to `anyplot.ai` + localhost.
- **MonoLisa Fallback**: `@font-face` with `local('Consolas'), local('Menlo'), local('Monaco'), local('DejaVu Sans Mono')` + size-adjust metrics — prevents CLS while the webfont loads.
- **No Google Fonts**: Fraunces and Inter were removed in favor of MonoLisa-only. ~40–60 KB transfer + one handshake saved.

### 5.2 Type Roles

The key rule: **mono is the default, italic-ss02 is the editorial accent.** Everything is MonoLisa. Upright for structure, italic (which triggers ss02 script glyphs) for emphasis. No second font.

| Element                | Variant           | Size                       | Weight | Notes                                                           |
|------------------------|-------------------|----------------------------|--------|-----------------------------------------------------------------|
| Display headlines      | mono + script     | `clamp(44, 4.5vw, 76px)`   | 400–700| Hero H1 mixes upright bold (code token) + italic-script (prose accent). |
| Section titles         | mono italic + ss02| `clamp(36, 4.5vw, 56px)`   | 300–400| Script variant on title word. Preceded by a shell prompt.       |
| Shell prompt prefix    | mono upright      | 0.6× section-title size    | 500    | `❯` `$` `~/path/` — `--ink-muted`, sits before the title.        |
| Body paragraph         | mono upright      | 14–16px                    | 300–400| Default body text. Lowercase preferred.                         |
| Intro / lede           | mono upright      | 18–19px                    | 300–500| Paragraph under H1. Subtitle (`one spec · every library…`) at 500. |
| Tagline                | mono italic + ss02| 18–22px                    | 400    | Script variant, e.g. `steal like an artist.`                    |
| Eyebrow / Kicker       | mono upright      | 11px                       | 400    | Lowercase, tracked `.08em`, preceded by a 18×1px green rule.    |
| UI labels & buttons    | mono upright      | 12–13px                    | 500    | Buttons lowercase, e.g. `browse plots →`.                       |
| Navigation links       | mono upright      | 14px                       | 500    | Active state: green `•` prefix.                                 |
| Code / logo            | mono upright      | context-dependent          | 700    | Logo: `any.plot()` with green dot and ghosted `()`.             |
| Stats / numerals       | mono upright      | 24–32px                    | 600    | Quiet support — no italic/green accents on numerals anymore.    |
| Emphasis in body       | mono italic + ss02| inherits                   | inherit| `<em>your</em>` reads as script within upright prose.           |
| Inline code in prose   | mono upright      | inherits ×0.95             | 500    | Background `--bg-elevated`, padding 2–4px, radius 3px.          |

### 5.3 Display Type Construction

The hero is a split-column layout: editorial text on the left (paper-tier), terminal-framed plot-of-the-day on the right (catalog-tier). The full-width "terminal box" around everything was dropped; the plot panel alone carries the terminal metaphor now.

```
— the open plot catalogue           ┌─ ~/anyplot ──────────────────┐
                                    │ $ python plots/…/plotly.py  │
any.plot()                          │                             │
— any library.                      │  [plot rendered here]       │
                                    │                             │
one spec · every library ·          │                             │
always current.                     │                             │
                                    │                             │
every plot begins as a              │                             │
library-agnostic spec…              │                             │
                                    │                             │
steal like an artist._▌             │                             │
                                    │                             │
[browse plots →]  or connect via    └─────────────────────────────┘
                  mcp / github →
────────────────────────────────────────────────────────────────
 1            9          310           2,677         441k
 languages    libraries  specifications implementations lines of code
```

**H1 construction (two lines):**
- Line 1: `any.plot()` — MonoLisa Bold (700), upright, with `.` in `--ok-green` (circle via `scale(1.3)`), ghosted `()` at opacity 0.45. This matches the NavBar logo exactly for brand consistency.
- Line 2: `— any library.` — MonoLisa italic + `ss02`, weight 400, same 0.75em size as `any.plot()` so heights align. The script variant reads as the editorial subline.
- Size: `clamp(2.75rem, 4.5vw, 4.75rem)` on the H1 container, with `0.75em` on both spans.

**Layer hierarchy (top to bottom, left column):**
1. **Eyebrow** — `— the open plot catalogue`, lowercase, 11px MonoLisa upright, `--ok-green`, tracked `.08em`, preceded by 18×1px green rule.
2. **H1** — see above.
3. **Subtitle** — `one spec · every library · always current.`, MonoLisa upright weight 500, 18px, `--ink`. Must fit on one line (`whiteSpace: nowrap` + stepped responsive size).
4. **Intro prose** — 4–6 lines MonoLisa upright weight 300, `--ink-soft`, 18px. `<em>your</em>` renders as italic-ss02 script accent inline.
5. **Tagline** — `steal like an artist.`, MonoLisa italic + `ss02`, 22px. Typed out by TypewriterText (see §8.1) at ~68ms/char, with a trailing green block cursor that fades 2.5s after typing completes.
6. **CTAs** — primary black pill `browse plots →`, two stacked text-links next to it: `or connect via mcp →`, `or clone on github →`. Lowercase throughout.
7. **NumbersStrip** — single `borderTop`, five quiet stats (1.5rem MonoLisa weight 600 in `--ink-soft`), labels 12px `--ink-muted`. Hangs directly under the hero inside the same 88svh section so the libraries peek below.

CSS sketch:

```css
.hero-h1 {
  font-family: var(--mono);
  font-size: clamp(2.75rem, 4.5vw, 4.75rem);
  line-height: 0.95;
  letter-spacing: -0.03em;
  color: var(--ink);
}
.hero-h1 .wordmark  { font-weight: 700; font-size: 0.75em; letter-spacing: -0.02em; }
.hero-h1 .dot       { background: var(--ok-green); border-radius: 50%; /* circle */ }
.hero-h1 .parens    { font-weight: 400; opacity: 0.45; }
.hero-h1 .accent    {
  font-style: italic;
  font-feature-settings: "ss02";   /* script variant */
  font-weight: 400;
  font-size: 0.75em;
  white-space: nowrap;
}
.hero-tagline       { font-style: italic; font-feature-settings: "ss02"; }
.hero-cursor        { width: 0.55em; background: var(--ok-green); animation: blink 1s steps(2) infinite; transition: opacity 0.6s; }
@keyframes blink { 50% { opacity: 0; } }
```

**NumbersStrip construction** (quiet proof-strip, not dominant numerals):
- Number in MonoLisa weight 600, 24–28px, `--ink-soft`, no italic, no accent color.
- Label below in MonoLisa lowercase 12px, `--ink-muted`, tracked `.04em`.
- Single `borderTop: 1px solid var(--rule)`, no bottom border (matches section-header convention).

### 5.4 Plot-internal Typography

Inside plot containers (axis labels, legends, annotations), use monospace throughout to keep plots consistent with the code-forward brand and align with how readers see plot labels in Jupyter notebooks and documentation.

- **Tick labels, legends, annotations**: MonoLisa or fallback monospace, 10–12px
- **Axis labels**: MonoLisa, 11–13px, `--ink-soft`
- **Plot titles**: MonoLisa, 13–15px, `--ink`, rendered outside the plot in the container header rather than inside the axes

---

## 6. Layout System

### 6.1 Three-tier Width System

Different page types deserve different widths. The system has three tiers:

| Tier            | Max width  | Used for                                                    |
|-----------------|------------|-------------------------------------------------------------|
| **paper**       | 1240px     | Landing hero box, About, Methodology, Blog, Legal           |
| **catalog**     | 2200px     | Plot catalog, search results, library pages, spec pages     |
| **hero-flank**  | full vw    | Landing hero side plot stacks (only ≥1600px viewport)       |

**Why three tiers:**

- **paper**: keeps reading line-length comfortable (60–80 chars) for editorial content
- **catalog**: lets ultrawide screens show many plot cards per row (the user came to browse — give them room)
- **hero-flank**: rewards ultrawide users with extra showcase content (vertical scrolling thumbnails) without compressing the paper-width hero

CSS sketch:

```css
.tier-paper   { max-width: 1240px; margin: 0 auto; padding: 0 var(--gutter); }
.tier-catalog { max-width: 2200px; margin: 0 auto; padding: 0 var(--gutter); }
.tier-flank   { width: 100vw; }   /* full viewport width, used by hero side stacks only */
```

**Other layout primitives:**

- **Gutter**: 24px on mobile, scaling to 96px on wide screens (set as `--gutter`)
- **Hero box**: paper-tier, terminal-style box (see §7.1) ~700–900px wide inside the paper container
- **Library grid (catalog tier)**: `repeat(auto-fill, minmax(280px, 1fr))` — responsive across the full 2200px

### 6.2 Spacing & Vertical Rhythm

- **Section padding**: 80px vertical on desktop
- **Hero sections**: 80–100px vertical
- **Card padding**: 24–28px internal

This is significantly more breathing room than most modern sites, and it's deliberate — see principle §2.1.5.

### 6.3 Section Header Pattern

Each section starts with a shell-prompt prefix that names the section as if it were a directory or command. The prompt sits inline with the section title:

```
❯ libraries
─────────────────────────────────────────────────────────
matplotlib   seaborn   plotly   bokeh   altair   ...

$ plots
─────────────────────────────────────────────────────────
[scatter-basic] [bar-grouped] [line-multi] ...

~/anyplot/about
─────────────────────────────────────────────────────────
```

- **Prefix glyph**: `❯` for navigation/categorical sections, `$` for action/list sections, `~/path/` for hierarchical/about/meta sections
- **Prefix font**: MonoLisa weight 500, color `--ink-muted`, scaled to ~0.6× the title size
- **Title font**: MonoLisa italic + `ss02` stylistic set, 1.6–2rem weight 400, `--ok-green` — the script variant reads as the editorial accent (e.g. `libraries`, `specs`)
- **Underline**: 1px solid `--rule`, full container width, sits 8–12px below the title baseline

The pattern reads as if the user just typed a command and got a section as output. It collapses the editorial "Section §01" framing into something more native to the visitor.

### 6.4 Masthead Rule

The site opens with a thin horizontal rule displaying:

```
~/anyplot.ai · main · v1.1.0 │ // the open plot catalogue. │ ◐ dark
```

Lowercase, monospace, three slots. The left slot shows the domain + git branch + current release tag (the tag is fetched live from the GitHub releases API with 24h localStorage cache); `main` links to the branch tree, the version links to the release page. The center slot is a code-comment-style sub-tagline. The right slot is a `◐` half-circle theme toggle. This bar immediately positions the site as a tool/publication hybrid rather than a marketing page, and puts the domain in view at all times.

### 6.5 Library Grid

In catalog tier (`max-width: 2200px`): `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`. On a 2200px viewport this yields ~7 cards per row (with default 280px min); on a 1280px viewport, ~4 cards. Responsive without explicit breakpoints.

---

## 7. Components

### 7.1 Hero Terminal Box (scoped to the plot panel)

**Status update**: The terminal-box framing no longer wraps the full hero. The left column is now plain editorial text; only the **plot-of-the-day panel on the right** keeps the terminal treatment (with a `~/anyplot` tab label and a `$ python …` prompt header). The CSS below still applies to that panel. See §5.3 for the current hero structure.

The plot panel sits inside a single ASCII-style box drawn with CSS borders. The box framing makes the panel feel like a terminal window rendered on editorial paper.

```
┌─ ~/anyplot ──────────────────────┐
│                                  │
│ ❯ any.plot() — any library.      │
│                                  │
│ get inspired.                    │
│ grab the code.                   │
│ make it yours._▌                 │
│                                  │
│ [.start()]  [.browse()]          │
│                                  │
└──────────────────────────────────┘
```

```css
.hero-box {
  position: relative;
  border: 1px solid var(--ink-muted);
  border-radius: 6px;       /* slight, terminal-window-like */
  background: var(--bg-surface);
  padding: 36px 40px 32px;
  font-family: var(--mono);
  max-width: 720px;
  margin: 0 auto;
}
.hero-box::before {
  content: "~/anyplot";
  position: absolute;
  top: -0.7em;
  left: 24px;
  padding: 0 10px;
  background: var(--bg-page);    /* punches through the border */
  font-size: 12px;
  color: var(--ink-muted);
  letter-spacing: 0.05em;
}
```

The `::before` pseudo-element ("`~/anyplot`") sits on top of the border line, like a tab label on a tmux pane or a fieldset legend. On dark mode the same construction works because `--bg-page` swaps automatically.

### 7.2 Plot Card

The fundamental display unit for any visualization:

```css
background: var(--bg-surface);
border: 1px solid var(--rule);
border-radius: 12px;
padding: 28px;
box-shadow: 0 1px 2px rgba(0,0,0,0.02),
            0 24px 48px -24px rgba(0,0,0,0.08);
```

Two-layer shadow: the first (`0 1px 2px`) gives a sharp edge that keeps the card visually anchored; the second (`0 24px 48px -24px`) is a soft ambient drop that suggests elevation without being heavy.

The card has three vertical zones:

```
┌──────────────────────────────────────┐
│ scatter-basic              ↗ open    │  ← header: mono slug + open-in-new icon
├──────────────────────────────────────┤
│                                      │
│   [ plot SVG area ]                  │
│                                      │
├── dashed rule ──────────────────────┤
│ matplotlib · 120 LOC                 │  ← footer: library + meta in mono-muted
│                                      │
│ .copy()  .open()  .download()        │  ← actions: code-style buttons (see §7.4)
└──────────────────────────────────────┘
```

The dashed rule between plot and footer differentiates the meta from the plot without drawing attention. Solid rules feel too structural for this role.

Action buttons appear on card hover (`opacity: 0 → 1`, 0.2s).

### 7.3 Library Card

Used in the catalogue grid. Similar to plot card but with specific additions:

- Top 2px accent bar, initially `scaleX(0)`, animates to `scaleX(1)` on hover (color varies per library via `--accent` custom property)
- Hover lifts card by 3px (`translateY`) and softens border toward brand green
- Mini-plot thumbnail uses SVG at fixed 120px height
- Library name in mono-bold, example count in mono-muted (`matplotlib · 142 plots`)

The color of the accent bar is a subtle way to give each library a personality without breaking the shared palette system — every library gets one of the Okabe-Ito colors as its accent.

### 7.4 Buttons

Three variants. All buttons read as method calls in mono — there is no ambiguity about what they do, and they don't need icons or tooltips to explain themselves.

**Action buttons (code-style — primary affordance throughout the site)**

```css
.btn-action {
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-muted);
  background: transparent;
  border: none;
  padding: 6px 10px;
  border-radius: 4px;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}
.btn-action::before { content: "."; color: var(--ink-muted); }
.btn-action:hover {
  color: var(--ok-green);
  background: var(--bg-elevated);
}
.btn-action:hover::before { color: var(--ok-green); }
```

Examples: `.copy()`, `.open()`, `.download()`, `.preview()`, `.share()`, `.fork()`, `.raw()`. The leading `.` is part of the visual language — it signals "this is a method on the thing in front of you" without saying so. No icons needed for common actions.

#### 7.4.1 Subject-Prefixed Method Calls

Two forms of the pseudo-function style, used in different contexts:

1. **Implicit subject — `.verb()`** — when a card or surrounding surface visually provides the subject (plot card, detail pane). See the button examples above.
2. **Explicit subject — `subject.verb()`** — when the action stands alone, detached from a carrier. Format follows `any.plot()`: the subject is the object/namespace (`--ink-muted`), `.verb()` is the method (`--ink`, green on hover).

Examples of the explicit form:

- Hero CTAs: `plots.browse()`, `plots.find()`
- Secondary links: `github.clone()`, `mcp.connect()`
- Search prompt: `❯ plots.find(_▌)` (or bare `.find()` inside a detail pane)
- Page-level fallbacks: `page.miss()`, `results.empty()`

Pluralisation: prefer the natural plural for collections (`plots.browse()`, `libs.list()`) and the singular for a specific item (`plot.open()`, `spec.copy()`). Keep everything lowercase — the wordmark-style capitalisation stops at the logo.

**Accessibility**: the pseudo-function style is a *visual* convention — it belongs on visible labels, tooltip titles, and placeholder text. `aria-label` and any hidden `<label>` fallback for assistive tech must stay in readable human language (`"Copy code"`, `"Browse plots"`, `"Zoom in"`), because screen readers announce punctuation literally (`.copy()` → "dot copy open close paren"). Icon-only controls should always carry a descriptive `aria-label` even when their tooltip uses the method-call style.

**Hero CTA (filled, only on landing hero)**

```css
.btn-cta {
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 500;
  background: var(--ink);
  color: var(--bg-page);
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 10px 16px;
  transition: background 0.2s, color 0.2s;
}
.btn-cta::before { content: "."; opacity: 0.6; }
.btn-cta:hover {
  background: var(--ok-green);
  color: #FFF;
}
.btn-cta:hover::before { opacity: 1; }
```

Used for `[.start()]` and `[.browse()]` in the hero box. Pill shape replaced with a more terminal-native rectangle (4px radius). Dark-to-green hover transition stays as the signature moment.

**Ghost (rare — only when a primary already occupies visual space)**

```css
.btn-ghost {
  font-family: var(--mono);
  font-size: 13px;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--rule);
  border-radius: 4px;
  padding: 8px 14px;
}
.btn-ghost:hover { border-color: var(--ink-muted); }
```

### 7.5 Side Plot Stacks (Ultrawide Hero)

The two vertical strips of plot thumbnails flanking the hero on ultrawide viewports. See §8.5 for the auto-scroll animation and viewport gating.

Container:

```css
.hero-flank {
  display: none;
  position: absolute;
  top: 0; bottom: 0;
  width: clamp(180px, 18vw, 320px);
  overflow: hidden;
  mask-image: linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
}
.hero-flank--left  { left: 0; }
.hero-flank--right { right: 0; }
@media (min-width: 1600px) { .hero-flank { display: block; } }
```

Each thumbnail in the stack:
- 1:1 aspect ratio, 12px border-radius
- Static plot image (PNG/SVG), no axes, no labels — pure visual
- Dimmed by default (`opacity: 0.5`), full opacity on hover
- Click navigates to the plot's spec page

### 7.6 Code Block

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

**Syntax highlighting** uses the Okabe-Ito palette:

- Keywords → sky blue
- Strings → brand green
- Function names → orange
- Comments → gray (`#666`, italic)
- Variables → purple
- Numbers → yellow (rare, because the cold Yellow works fine on dark bg)

### 7.7 Navigation

Horizontal text links, no icons, no boxes. On hover, a 1px green underline animates in from the left. On active state, a small green bullet (`•`) appears 12px to the left of the text.

```css
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
```

The `cubic-bezier(0.4, 0, 0.2, 1)` is the standard material-motion "ease-in-out" curve — smooth but with enough snap to feel crisp.

### 7.8 Search Affordance

Top-right of the nav, styled as an inline mono input that reads `❯ .find(_)` with a `⌘K` hint badge to its right. Borderless until hover. Clicking opens a command palette which expands the cursor and accepts typing — the user feels they're continuing the same line of code.

```
❯ .find(_▌)        ⌘K
```

Active palette state replaces the placeholder cursor with the user's typed query, still in mono. Results appear below the input as a list of `slug · library · tags` lines, each prefixed with `❯` to maintain the prompt continuity.

---

## 8. Animation

Restrained. Five categories.

### 8.1 Page Load

Hero box rises from 8px below with opacity transition:

```css
@keyframes rise {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

Staggered via `animation-delay`:

- Eyebrow (`— the open plot catalogue`): 0s
- H1 line 1 (`any.plot()`): 0.1s
- H1 line 2 (`— any library.` script): 0.1s
- Subtitle (`one spec · every library · always current.`): 0.15s
- Intro paragraph: 0.2s
- Tagline (TypewriterText, typed at ~68ms/char; cursor fades 2.5s after done): 0.25s
- CTAs: 0.3s
- Plot-of-the-day terminal panel (right column): 0.3s

Total initial cascade: ~0.8s, plus the tagline types for another ~1.4s. The TypewriterText effect on the tagline is what makes the hero feel like code being written out; no per-line triplet animation anymore.

### 8.2 Hero Cursor (Blinking)

The block cursor at the end of `make it yours._▌` blinks indefinitely:

```css
.hero .cursor {
  display: inline-block;
  width: 0.6em;
  height: 1em;
  background: var(--ok-green);
  vertical-align: -0.1em;
  animation: blink 1s steps(2) infinite;
}
@keyframes blink { 50% { opacity: 0; } }
```

Use `steps(2)` rather than a smooth ease — terminal cursors are square-wave, not sinusoidal. A fading cursor reads as decorative; a square-blinking one reads as terminal.

### 8.3 Optional: Hero Typing Animation

For the page-load sequence, the triplet lines may type themselves character-by-character at ~40 chars/second, with the cursor following the typed character. Disable on `prefers-reduced-motion` and on subsequent visits (cookie-flag the first visit). If implemented, the staggered delays in §8.1 are replaced by sequential typing completion.

```css
@media (prefers-reduced-motion: reduce) {
  .hero .typed { animation: none !important; }
  .hero .cursor { animation: none; opacity: 1; }
}
```

### 8.4 Hover States

All transitions use 0.15–0.3s with `cubic-bezier(0.4, 0, 0.2, 1)`. Never use default `ease` — it's too linear for modern motion.

### 8.5 Side Plot Stacks (Ultrawide Hero)

The vertical plot stacks flanking the hero box on ultrawide viewports auto-scroll continuously:

```css
.hero-flank {
  display: none;            /* hidden by default */
  height: 100vh;
  overflow: hidden;
  mask-image: linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
}
@media (min-width: 1600px) {
  .hero-flank { display: block; }
}
.hero-flank__track {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: flank-scroll 60s linear infinite;
}
@keyframes flank-scroll {
  from { transform: translateY(0); }
  to   { transform: translateY(-50%); }    /* track contains plots×2; loops seamlessly */
}
.hero-flank:hover .hero-flank__track { animation-play-state: paused; }
```

- Two stacks, one each side of the hero box
- Each stack: 8–12 plot thumbnails sampled randomly from the catalog at page load
- Top/bottom 10% fade to transparent (mask-image) so plots dissolve in/out rather than hard-cutting
- Hover anywhere on a stack pauses the scroll (so the user can click through to a plot)
- Disabled on `prefers-reduced-motion`

### 8.6 Palette Strip Interaction

The palette strip at the bottom responds to hover: normal state is even distribution, `:hover .sw` shrinks all colors to 50%, then `.sw:hover` expands the specific hovered color to 300%. Playful detail that invites interaction without being necessary.

```css
.palette-strip .sw { flex: 1; transition: flex 0.3s; }
.palette-strip:hover .sw { flex: 0.5; }
.palette-strip .sw:hover { flex: 3; }
```

---

## 9. Plot Style

### 9.1 Color Defaults

- **First series = brand color (`#009E73`)**. Always. This is the single most important consistency rule.
- **Neutral (position 8) is reserved** for aggregates, residuals, and reference lines. Don't use it for a normal category unless you've exhausted the other seven.
- **Yellow (`#F0E442`) on white backgrounds** has poor contrast. Use it only for position 7 or later, never for thin lines or small markers.

### 9.2 Non-categorical Data

Okabe-Ito is a **categorical** palette — it's for distinct categories, not ordered or continuous data. For other data types:

- **Sequential (single-variable magnitude)**: use `viridis` or `cividis`. Both are perceptually uniform and colorblind-safe. `cividis` is additionally optimized for print.
- **Diverging (two-sided, midpoint-anchored)**: use `BrBG` (brown-to-bluish-green) from ColorBrewer, or construct one centered on a neutral tone.
- **Heatmaps**: use `viridis` for general-purpose, `Reds`/`Blues` for single-polarity intensity.

Don't reach for Okabe-Ito for these cases — a categorical palette on continuous data produces misleading banding artifacts.

### 9.3 Plot Container Surfaces

Plot containers use `--bg-surface` with a 1px border (`rgba(0,0,0,0.08)` on light, `rgba(255,255,255,0.08)` on dark) and 12–24px border-radius depending on context. The subtle elevation differentiates plots from page content without harsh boundaries.

### 9.4 Validation

Every palette change should be validated against:

- **Deuteranopia** (red-green confusion, most common CVD, ~6% of men)
- **Protanopia** (red-weak, ~1% of men)
- **Tritanopia** (blue-yellow confusion, rare but important)

Recommended tools:

- [Viz Palette](https://projects.susielu.com/viz-palette) — interactive CVD simulator for palettes
- [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/) — upload a plot image, see all three simulations
- [Sim Daltonism](https://michelf.ca/projects/sim-daltonism/) — macOS system-wide CVD simulator
- [Colour Science for Python](https://www.colour-science.org/) — programmatic access to Machado et al. (2009) simulation matrices

For algorithmic palette generation beyond Okabe-Ito, see Petroff (2021) — a more recent palette optimized with numerical solvers in the CAM02-UCS perceptual color space.

### 9.5 Implementation Reference

The palette is exposed in the Python library as:

```python
import anyplot as ap

# full palette as list
ap.palettes.okabe_ito              # returns list of 8 hex strings

# by role name
ap.palettes.okabe_ito.brand        # "#009E73"
ap.palettes.okabe_ito.vermillion   # "#D55E00"
ap.palettes.okabe_ito.blue         # "#0072B2"
# ...

# theme-aware neutral
ap.palettes.okabe_ito.neutral("light")   # "#1A1A1A"
ap.palettes.okabe_ito.neutral("dark")    # "#E8E8E0"

# as matplotlib cycler
import matplotlib.pyplot as plt
plt.rcParams['axes.prop_cycle'] = ap.palettes.okabe_ito.cycler()
```

For CSS:

```css
:root {
  --ap-green:      #009E73;
  --ap-vermillion: #D55E00;
  --ap-blue:       #0072B2;
  --ap-purple:     #CC79A7;
  --ap-orange:     #E69F00;
  --ap-sky:        #56B4E9;
  --ap-yellow:     #F0E442;
  --ap-neutral:    #1A1A1A;  /* adaptive */
}

@media (prefers-color-scheme: dark) {
  :root { --ap-neutral: #E8E8E0; }
}
```

---

## 10. Anti-patterns

### 10.1 Visual

- **Gradients**: especially purple-to-blue SaaS gradients. The palette is categorical; continuous gradients would undermine its logic.
- **Glass morphism / backdrop-blur**: too trendy, breaks the paper metaphor.
- **Tech-startup illustrations**: isometric figures, 3D renders, hand-drawn doodles — all wrong register.
- **Parallax effects or hero videos**: too heavy for a content-first site. Layout should feel instantly complete.
- **Badge-heavy UI**: "NEW!" badges, notification dots, progress indicators competing for attention. Reserve attention for plots.
- **Pure white or pure black backgrounds**: harsh, removes the warmth, makes plots look awkward against them.
- **Branded loading spinners**: a plain loading indicator is fine. A branded animated logo is overkill.
- **Generic stock imagery**: no isometric illustrations, no people high-fiving, no laptop-on-desk hero shots. Plots are our imagery.
- **A second typeface**: no Space Grotesk, no Poppins, no Fraunces, no Inter. MonoLisa is the only face; italic + `ss02` is the only "second voice." Reaching for a serif for warmth or a sans for legal text undoes the single-face discipline.

### 10.2 Brand

- **Overclaiming**: "The best plotting catalogue." We're not. We're a plotting catalogue. Let readers decide if it's best.
- **Tech-hype vocabulary**: "Supercharge", "unlock", "revolutionary", "game-changing", "AI-powered." All out.
- **Fake urgency**: "Don't miss out!" "Get started today!" — we're not selling anything.
- **Inconsistent casing**: headings that alternate between Title Case and lowercase within the same context look like nobody decided.
- **Testimonials from non-existent users**: we don't need social proof theatre.
- **Cookie banners beyond what's legally required**: we don't track users. The privacy footer says so.

### 10.3 Color

- **Purple (`#CC79A7`), Sky (`#56B4E9`), or Yellow (`#F0E442`) in UI chrome.** These are plot-only colors. Using them in navigation or buttons breaks the color hierarchy.
- **Brand green in backgrounds, body text emphasis, or non-logo icons.** Reserve `#009E73` for the seven approved contexts (§4.4).
- **Categorical palettes on continuous data.** Use viridis/cividis/BrBG instead — see §9.2.

---

## 11. Reference Files & Implementation

The design system is implemented across:

- **HTML reference (full mockup)**: `mockups/landing.html` — single-file reference with all sections, SVG plots, and animations
- **Theme tokens (frontend)**: `app/src/theme/index.ts` and `app/src/main.tsx` — MUI theme exports for colors, typography, spacing, headingStyle, subheadingStyle, textStyle, tableStyle, codeBlockStyle
- **Palette (Python library)**: `anyplot.palettes.okabe_ito` — see §9.5

**Reference CSS skeleton:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>anyplot.ai — any library. one plot.</title>
  <link rel="preconnect" href="https://storage.googleapis.com" crossorigin>
  <!-- MonoLisa basic-latin preload (variable font, all weights in one file) -->
  <link rel="preload" href="https://storage.googleapis.com/anyplot-static/fonts/0-MonoLisa-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="https://storage.googleapis.com/anyplot-static/fonts/2-MonoLisa-normal.woff2" as="font" type="font/woff2" crossorigin>
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

      /* Typography — MonoLisa only. serif/sans aliased for compatibility. */
      --serif: 'MonoLisa', 'MonoLisa Fallback', Consolas, Menlo, Monaco, monospace;
      --sans:  'MonoLisa', 'MonoLisa Fallback', Consolas, Menlo, Monaco, monospace;
      --mono:  'MonoLisa', 'MonoLisa Fallback', 'JetBrains Mono', Consolas, monospace;

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

    /* Global: enable ss02 so any italic text renders as the script variant. */
    html { font-feature-settings: "ss02"; }

    body {
      font-family: var(--mono);
      background: var(--bg-page);
      color: var(--ink);
      font-size: 16px;
      line-height: 1.5;
      transition: background 0.3s, color 0.3s;
    }
  </style>
</head>
<body>
  <!-- Content goes here. See full reference file for complete markup. -->
</body>
</html>
```

---

## 12. Channels & Voice Adaptation

**Website.** Voice as described in §3.4–3.6 — precise, understated, lowercase default. The landing page reads more like a journal essay than a product pitch.

**GitHub README.** Slightly more technical. Use lowercase headings for a consistent feel. Include: logo at top (SVG), one-paragraph description, installation instructions (first thing below the description), quick-start code example, link to documentation, license and citation. Do not include badges for every CI status; that's noise. Only include badges that carry real information.

**Documentation (docs.anyplot.ai).** More formal than the marketing site. Follow the same visual style but with denser information layouts. Code blocks dominate. Each function has: one-line description, parameters table, at least one example, related functions (see-also).

**Social media.** Rare. We're not a company that needs to post daily. Use social channels for: announcing new library support, pointing to particularly interesting examples, linking to related technical writing. Tone: informational, not promotional. Include a plot image whenever possible. Avoid self-reference ("check out our new...") — state the thing itself ("matplotlib now supports...").

**Academic citation:**

```
anyplot.ai. (2026). A catalogue of Python plotting examples
across multiple libraries. https://anyplot.ai
```

Eventually, once the project is mature, consider writing a JOSS (Journal of Open Source Software) paper so there's a formal citation target.

**Non-web visual identity:**

- **GitHub profile images**: square variant of the logo: `any.plot()` in MonoLisa Bold, centered, on warm off-white background (`#F5F3EC`). Green dot at `#009E73`. Maintain 1em padding from edges.
- **OG / Twitter card images**: 1200×630px. Top-left: `anyplot.ai` logo in MonoLisa Bold. Center-left: page title in MonoLisa — bold upright for the subject, italic + ss02 script for one accent word. Center-right: representative plot screenshot or palette strip. Bottom: minimal meta in mono.
- **Presentations**: black or warm off-white backgrounds. MonoLisa throughout — upright for body, italic-script for section dividers. Brand green only for emphasis. Every plot in the deck uses Okabe-Ito.
- **T-shirts / merch (if ever)**: dark t-shirt, `any.plot()` in white with green dot, centered on chest. No taglines, no URLs, no GitHub handles. One variant only.

---

## 13. Reference Points

Aesthetic directions we drew from:

- **observablehq.com** — scientific, plot-centered, monospace details
- **arXiv preprints** — the "considered paper" feel we're targeting
- **Wes Anderson film posters** — for the principle of warm neutrals with sparing, saturated color accents
- **The New York Times' interactive features** — for the editorial layout rhythm
- **Vercel's documentation** — for the clean monospace-heavy technical pages

What we explicitly didn't borrow from:

- Generic SaaS landing pages (Stripe, Linear, Notion)
- AI startup aesthetics (Anthropic site, OpenAI site, HuggingFace)
- Tech-product marketing pages (Vercel's homepage, specifically — too dense with features)

---

## 14. Academic References

1. Okabe, M. & Ito, K. (2008). *Color Universal Design (CUD): How to make figures and presentations that are friendly to colorblind people.* Jikei Medical School / University of Tokyo. [https://jfly.uni-koeln.de/color/](https://jfly.uni-koeln.de/color/)

2. Wong, B. (2011). *Points of view: Color blindness.* Nature Methods 8, 441. [https://doi.org/10.1038/nmeth.1618](https://doi.org/10.1038/nmeth.1618) — extends Okabe-Ito with publication-specific usage guidelines.

3. Machado, G. M., Oliveira, M. M. & Fernandes, L. A. F. (2009). *A physiologically-based model for simulation of color vision deficiency.* IEEE Transactions on Visualization and Computer Graphics 15(6), 1291–1298. — the simulation model used by most modern CVD validators.

4. Petroff, M. A. (2021). *Accessible Color Sequences for Data Visualization.* arXiv:2107.02270. — modern alternative using CAM02-UCS optimization; relevant if green is not a required anchor.

5. Brewer, C. A. (2003). *ColorBrewer in Print: A Catalog of Color Schemes for Maps.* Cartography and Geographic Information Science 30(1). [https://colorbrewer2.org](https://colorbrewer2.org) — the gold standard for cartographic color schemes, useful for reference beyond categorical palettes.

6. van der Walt, S. & Smith, N. (2015). *A Better Default Colormap for Matplotlib.* SciPy 2015. — the paper behind `viridis`, the recommended sequential colormap.

---

## Maintenance

This document is the canonical design system reference. Deviations should be discussed and either:

1. Rejected (system holds)
2. Accepted as one-off exceptions (documented inline in code with a comment)
3. Accepted as new standards (this document is updated)

Option 3 is the healthy path for small refinements. This is a living document, not a contract.

*Last updated: 2026.*
