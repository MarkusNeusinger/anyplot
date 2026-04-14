# Brand Guide

The **anyplot.ai** brand identity — logo, name, voice, and how we talk about what we do. This document covers the parts of the brand that aren't strictly visual: naming conventions, tone of voice, positioning, and the stories we tell about the project.

Pair this with `plot-style-guide.md` (color system) and `frontend-design-guide.md` (website design) for the complete design system.

## TL;DR

**anyplot.ai** is a curated catalogue of Python plotting examples across nine libraries, sharing one colorblind-safe palette. The brand is positioned as a **considered reference work** for developers who care about data visualization — more like an academic journal than a software product, more like a cookbook than a SaaS. Technical, precise, lowercase by default, with a small green dot as the single memorable visual mark.

## The name

### anyplot.ai

The name carries three ideas:

**"any"** — library-agnostic. You can plot anything with anyplot, whether that means matplotlib, seaborn, plotly, or whatever library you prefer. Not "py" (Python-specific) because the project's long-term vision extends beyond one language.

**"plot"** — the core object. We're not abstracting away the plot; we're cataloguing it. The word anchors us in the data visualization domain.

**".ai"** — the modern TLD, inherited from `pyplots.ai`. It signals "contemporary technical project" without claiming AI-generated content. (We use AI to generate examples, but that's a production detail, not the brand.)

### Pronunciation

**"any-plot dot AI"** — three distinct words, not "any-plottie". The dot is pronounced because the domain structure matters.

Alternative casual forms:
- "anyplot" (when domain isn't needed)
- "ap" (in code: `import anyplot as ap`)

### Relationship to pyplots.ai

`pyplots.ai` is the predecessor. When anyplot launches, pyplots redirects with a 301 on every URL path (not just the domain root) so SEO signals transfer properly. The old domain stays registered for at least 3–5 years to prevent squatters from capturing residual traffic.

The rebrand is communicated as evolution, not replacement:

> anyplot.ai is the next chapter of pyplots.ai — broader in scope (beyond Python), broader in language (beyond English), and anchored in a colorblind-safe palette that travels across every library.

## The logo

### Primary wordmark

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

### Geometry

```
┌───────────────────────────────────────┐
│                                       │
│       any . plot()                    │
│          ^                            │
│          └── green, scale(1.45)       │
│                                       │
└───────────────────────────────────────┘

letter-spacing: -0.02em  (slight negative tracking for density)
font-weight:    700 (bold) for letters, 400 (regular) for parens
```

### Sizes

| Context           | Size       | Notes                           |
|-------------------|-----------|---------------------------------|
| Favicon / app icon| 16–64px   | Reduce to `a.p` — keeps the dot |
| Top-nav           | 18–22px   | Standard use                    |
| Hero section      | 40–64px   | Occasional, paired with headline|
| Large display     | 80–96px+  | Landing hero, posters           |

### Color variants

The logo adapts to context:

- **On light background**: ink-dark letters, green dot — default
- **On dark background**: ink-light letters, green dot stays the same
- **On brand green background**: do not use — too little contrast. Use monochrome white version instead.
- **Monochrome**: all letters in `--ink`, dot also in `--ink`. Used in print, fax-friendly contexts, and the occasional t-shirt.

### What the logo is not

The logo is **not** an illustration, icon, or mascot. We don't have a plot-graph silhouette, a Python-snake variant, or an anthropomorphic data point. The typographic wordmark is the entire brand mark. Resist the urge to add visual flourishes.

### Spacing / clear space

Maintain clear space of at least `1em` (one letter-height) around the wordmark on all sides. Inside the clear space, no other text, graphics, or UI elements may appear.

## Taglines

Primary: **any library. one plot.**

This is the canonical tagline. Three words, two sentences, mirrors the product proposition exactly. Use this in:

- Meta description
- README headline
- Business cards (if we ever make them)
- Footer
- Social media bios

### Alternative taglines for specific contexts

- **"a catalogue of scientific plotting"** — editorial framing, good for landing page subtitles
- **"from anyplot import *"** — code-playful, good for dev-audience posts
- **"1000+ plots. one import away."** — benefit-focused, good for blog intros
- **"plots that everyone can see"** — accessibility-focused, good for technical articles about colorblind safety

Rotate between these as appropriate for context. Primary tagline is always the canonical one.

### Taglines we explicitly don't use

- "the future of data visualization" (overclaim)
- "AI-powered plotting catalogue" (misleading — AI generates examples, but the site is a catalogue, not an AI tool)
- "plot anything, anywhere, anytime" (cliché, generic)
- "the GitHub of plots" (imitative framing)

## Voice

### Tone attributes

The brand voice is:

1. **Precise** — we say exactly what we mean, with the right technical terminology
2. **Understated** — we let the work speak; we don't overhype
3. **Curious** — we share interesting details and reasoning, not just conclusions
4. **Respectful of the reader** — we assume technical literacy without being condescending
5. **Slightly playful** — the occasional small joke, mostly structural (the method-call logo, the `import anyplot as ap` alias)

### Tone attributes we avoid

- **Sales-y** — no "unlock", "supercharge", "revolutionary", "game-changing"
- **Corporate** — no "solutions", "leverage", "empower", "synergies"
- **Breathless** — no excessive exclamation marks, no "literally" or "amazing"
- **AI-hype** — no "powered by AI", "intelligent", "smart"
- **Emoji-heavy** — we avoid emojis in documentation and formal writing; occasional use in social posts is fine

### Capitalization

**Default: lowercase.** UI labels, section titles, taglines, button text — all lowercase unless there's a specific reason.

Reasons to use uppercase:

- Proper nouns (library names like `matplotlib` are lowercase because that's how they're written; `GitHub` is uppercase because that's how it's written — follow upstream conventions)
- First word of a sentence in long-form prose
- Proper names of people or places
- Code identifiers that are uppercase in their original context

The lowercase default matches the code-forward aesthetic and keeps the site feeling quiet. "libraries" and "catalogue" and "palette" in a nav row all lowercase looks intentional; mixed casing would look like it wasn't decided.

### Punctuation

- **Oxford comma**: yes, always (we write for a technical audience that tends to appreciate grammatical clarity)
- **Em-dashes**: used freely for parenthetical asides — like this — with spaces around them (European style)
- **Sentence structure**: prefer short, declarative sentences. Longer sentences are fine when the content demands it.
- **Questions**: rare. We usually state things rather than ask them.

### Example transformations

Instead of:

> 🚀 Supercharge your data viz workflow with AI-powered plot generation! Unlock 1000+ beautifully crafted charts across multiple libraries. Ship faster, iterate smarter, and empower your team to create stunning visualizations!

Write:

> A catalogue of 1,000+ plotting examples across nine Python libraries. Every example uses the same colorblind-safe palette, so switching libraries never breaks your color grammar.

The second version is 40% shorter, contains more actual information, and reads as if written by someone who cares about what they're building.

## Positioning

### What anyplot is

- A **reference catalogue**, like a cookbook or an atlas. You come for specific examples.
- **Library-agnostic**, showing the same chart types across matplotlib, seaborn, plotly, and others.
- **Colorblind-safe by default**. Every example uses the Okabe-Ito palette. This isn't a feature, it's a baseline.
- **Copyable**. Every example is self-contained, with the full code visible and executable.
- **Curated**. We don't aggregate every plot on the internet — we maintain a considered collection.

### What anyplot is not

- **A plotting library**. We don't compete with matplotlib or plotly. We help you use them better.
- **An AI plot generator**. AI generates the examples behind the scenes; users don't prompt the AI directly.
- **A dashboard tool**. We show static examples. Interactive dashboards are a different product category.
- **A tutorial platform**. We assume you know how to run Python code. We don't teach from zero.
- **A community forum**. We accept contributions through GitHub but we're not building a social layer.

### Competitive framing

We're positioned alongside — not against — existing resources:

- **Matplotlib's official gallery** — the closest analog. Ours differs by spanning multiple libraries and enforcing palette consistency.
- **The Python Graph Gallery** — a blog-style resource. Ours differs by having no ads, no affiliate links, and a shared color grammar.
- **seaborn / plotly galleries** — library-specific. Ours is multi-library.
- **Observable notebooks** — JavaScript-focused, interactive. Ours is Python-focused, static.

If asked "why does this need to exist?": because every existing resource is either single-library, inconsistent in palette, cluttered with ads, or in a different language ecosystem. A unified, quiet, multi-library reference didn't exist.

## Story points

Things to mention when talking about anyplot. These are the narrative hooks:

### The palette story

> Every plot uses the Okabe-Ito palette, peer-reviewed for colorblind safety and designed for scientific publications in 2008. About 8% of men have some form of color vision deficiency — most plotting libraries ignore this entirely. We make it the default.

### The library-agnostic story

> A "Gentoo penguin" is always blue, whether you draw it in matplotlib, plotly, or bokeh. The palette travels with you across libraries. Switching tools doesn't mean re-learning your color grammar.

### The catalogue story

> A thousand examples across nine libraries, each reproducible and copy-pasteable. No ads. No affiliate links. No "suggested tutorials you might like." Just the plots and the code that made them.

### The origin story

> It started as pyplots.ai, a small Python-only catalogue I built in a weekend. It grew when I realized people wanted the same examples across different libraries, and the same safe palette everywhere. anyplot is the grown-up version.

### The personal touch

> Built in Visp, a small town in the Swiss Alps. By a data analyst who spent too many hours trying to figure out why the same chart looked different in seaborn than in plotly.

Use these as appropriate. Don't recite them verbatim — adapt to context and audience.

## Naming conventions

### The library

- **Package name**: `anyplot` (lowercase, one word)
- **Import convention**: `import anyplot as ap`
- **Sub-modules**: `anyplot.mpl`, `anyplot.plotly`, `anyplot.bokeh`, etc. — one sub-module per supported library
- **Palettes**: `anyplot.palettes.okabe_ito`, `anyplot.palettes.viridis`, etc.
- **Datasets**: `anyplot.load("penguins")`, `anyplot.load("iris")` — not `load_penguins()`; consistent loader signature

### The domain

- **Primary**: `anyplot.ai`
- **Language redirects**: `python.anyplot.ai` → `anyplot.ai/python/`, etc. (marketing-friendly, SEO-safe)
- **Documentation**: `docs.anyplot.ai` (planned)
- **GitHub org**: `anyplot` or `anyplot-ai` (to be decided on registration)

### Examples and identifiers

Each plot example has:

- A **slug** (URL-safe): `matplotlib-scatter-penguins-species`
- A **title** (human-readable): `Scatter plot of penguin species`
- A **library**: one of the nine supported
- **Tags**: chart type, data domain, complexity level

Slugs are the canonical identifier. They're used in URLs, filenames, and `ap.load()` calls.

## Channels and voice adaptation

### Website

Voice as described above — precise, understated, lowercase default. The landing page reads more like a journal essay than a product pitch.

### GitHub README

Slightly more technical. Use lowercase headings for a consistent feel. Include:

- Logo at top (SVG)
- One-paragraph description
- Installation instructions (first thing below the description)
- Quick-start code example
- Link to documentation
- License and citation

Do not include badges for every CI status; that's noise. Only include badges that carry real information (PyPI version, test coverage if it's high and stable).

### Documentation (docs.anyplot.ai)

More formal than the marketing site. Follow the same visual style but with denser information layouts. Code blocks dominate. Each function has:

- One-line description
- Parameters table
- At least one example
- Related functions (see-also)

### Social media

Rare. We're not a company that needs to post daily. Use social channels for:

- Announcing new library support
- Pointing to particularly interesting examples
- Linking to related technical writing

Tone: informational, not promotional. Include a plot image whenever possible. Avoid self-reference ("check out our new...") — state the thing itself ("matplotlib now supports...").

### Academic citation

If anyplot is used in a paper or publication, provide a clear citation:

```
anyplot.ai. (2026). A catalogue of Python plotting examples
across multiple libraries. https://anyplot.ai
```

Eventually, once the project is mature, consider writing a JOSS (Journal of Open Source Software) paper so there's a formal citation target.

## Visual identity in non-web contexts

### GitHub profile images

Use a square variant of the logo: `any.plot()` in MonoLisa Bold, centered, on warm off-white background (`#F5F3EC`). Green dot at `#009E73`. Maintain 1em padding from edges.

### OG / Twitter card images

1200×630px, following the website's typography hierarchy:

- Top-left: `anyplot.ai` logo
- Center-left: page title in Fraunces serif, italic accent on one word
- Center-right: representative plot screenshot or palette strip
- Bottom: minimal meta (author, date) in mono

Dark mode and light mode variants both acceptable.

### Presentations / slide decks

Use a simplified version:

- Black or warm off-white backgrounds
- Sans-serif (Inter or MonoLisa) body
- Fraunces for section dividers
- Brand green only for emphasis and single accent lines
- Every plot in the deck uses the Okabe-Ito palette, regardless of source library

### T-shirts / merch (if ever)

- Dark t-shirt, `any.plot()` in white with green dot, centered on chest
- No taglines, no URLs, no GitHub handles
- One variant only — don't over-merchandise

## Voice examples (do / don't)

**Announcing a new library:**

Do: `plotnine support just landed. 74 new examples using the grammar of graphics.`

Don't: `🎉 Big news! We're excited to announce that plotnine is now fully supported on anyplot.ai! Check out our awesome new collection of 74 examples! 🚀`

**Error message in the library:**

Do: `unsupported library: "ggplot". supported libraries are: matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, hvplot, datashader.`

Don't: `Oops! Looks like we don't support "ggplot" yet. But don't worry — we're always adding new libraries! 🙂`

**Changelog entry:**

Do: `v0.4.0 — added support for altair; palette exports now accept a theme argument (light/dark); fixed a bug where seaborn examples omitted legends.`

Don't: `🎉 v0.4.0 is here! We've been working hard to bring you some amazing new features...`

**GitHub issue response to a feature request:**

Do: `interesting idea. I'm not sure it fits the catalogue scope — anyplot focuses on static examples, and this would require interactive features. keeping it open for discussion.`

Don't: `Thanks so much for this amazing feature request!! ❤️ We'll definitely consider this for our roadmap!`

The pattern: state the position, state the reasoning, don't inflate the language.

## Anti-patterns across the brand

Things that consistently break the brand:

1. **Overclaiming.** "The best plotting catalogue." We're not. We're a plotting catalogue. Let readers decide if it's best.
2. **Tech-hype vocabulary.** "Supercharge", "unlock", "revolutionary", "game-changing", "AI-powered." All out.
3. **Fake urgency.** "Don't miss out!" "Get started today!" — we're not selling anything.
4. **Generic stock imagery.** No isometric illustrations, no people high-fiving, no laptop-on-desk hero shots. Plots are our imagery.
5. **Inconsistent casing.** Headings that alternate between Title Case and lowercase within the same context look like nobody decided.
6. **Branded-loading-spinners.** A plain loading indicator is fine. A branded animated logo is overkill.
7. **Testimonials from non-existent users.** We don't need social proof theatre.
8. **Cookie banners beyond what's legally required.** We don't track users. The privacy footer says so.

## Contact and maintenance

This document is the canonical brand reference. Deviations should be discussed and either:

1. Rejected (brand holds)
2. Accepted as one-off exceptions (documented inline)
3. Accepted as new standards (this document is updated)

Option 3 is the healthy path for small refinements. This is a living document, not a contract.

---

*Last updated: 2026. Paired with `plot-style-guide.md` and `frontend-design-guide.md` to form the complete anyplot.ai design system.*
