# Library Expansion Roadmap

Strategic overview for expanding anyplot beyond Python into a true multi-language
gallery. This document estimates the global market for charting libraries,
ranks candidates by reach and integration cost, and recommends a concrete
priority order.

> **Note on numbers.** The percentages below are *estimates* synthesised from
> public signals (Stack Overflow Developer Survey, PyPI/npm download counts,
> GitHub stars, Google Trends, JS Rising Stars). They are good enough to
> prioritise — they are not authoritative market shares.

---

## 1. Current state

anyplot currently ships **9 Python libraries** and zero non-Python libraries.

| # | Library    | Native     | In anyplot as | Most-used variant | Notes                                       |
|---|------------|------------|---------------|-------------------|---------------------------------------------|
| 1 | Matplotlib | Python     | Python        | Python            | Native = most-used.                         |
| 2 | Seaborn    | Python     | Python        | Python            | Built on matplotlib.                        |
| 3 | Plotly     | JavaScript | Python        | **Python**        | PyPI ~18 M / wk vs `plotly.js` ~0.8 M / wk. |
| 4 | Bokeh      | Python     | Python        | Python            | Native = most-used.                         |
| 5 | Altair     | Python     | Python        | Python            | Python interface to Vega-Lite (JSON spec).  |
| 6 | plotnine   | Python     | Python        | Python            | Sister library to ggplot2, not a wrapper.   |
| 7 | Pygal      | Python     | Python        | Python            | Native = most-used.                         |
| 8 | Highcharts | JavaScript | Python        | **JavaScript**    | npm ~1 M / wk vs `highcharts-core` ~5 k / wk.|
| 9 | lets-plot  | Kotlin     | Python        | Python            | Python front-end has the most users today.  |

**Implication:** under the most-used rule (see §6), only **Highcharts** is
filed under the wrong language and should move to JavaScript. Plotly and
lets-plot are correctly filed as Python despite not being native.

---

## 2. Language candidates — share of charting demand

Estimated split of global "charting library" usage across languages.
Calibrated against Stack Overflow tag traffic, package-manager downloads, and
job postings mentioning data-viz tooling.

| Rank | Language              | Share | Why it matters                                                               |
|------|-----------------------|------:|------------------------------------------------------------------------------|
| 1    | **Python**            | ~45 % | Data science default; already covered.                                       |
| 2    | **JavaScript / TS**   | ~35 % | Every dashboard, every embed, every BI tool. The biggest gap today.          |
| 3    | **R**                 | ~10 % | Statistics, academia, biotech, finance research.                             |
| 4    | Julia                 |  ~2 % | Scientific computing, growing slowly.                                        |
| 5    | Kotlin / JVM (Java)   |  ~2 % | Android dashboards, JVM backends; lets-plot lives here.                      |
| 6    | C# / .NET             |  ~2 % | Enterprise dashboards (LiveCharts, ScottPlot).                               |
| 7    | Go, Rust, Swift, etc. |  ~2 % | Niche; not enough demand to justify dedicated entries yet.                   |
| 8    | MATLAB                |  ~2 % | Declining, paid, closed ecosystem — not worth integrating.                   |

**Take-away:** JavaScript alone is bigger than R + everything else combined.
That is the single highest-impact direction.

---

## 3. JavaScript / TypeScript candidates

Estimated share *within* JS charting demand. (npm downloads + GitHub stars +
"<library> chart" search trends.)

| Library              | Share  | License     | Type            | Native? | Notes                                                                |
|----------------------|-------:|-------------|-----------------|---------|----------------------------------------------------------------------|
| **Chart.js**         | ~26 %  | MIT         | Canvas, simple  | yes     | The default for "I need a chart on a webpage."                       |
| **D3.js**            | ~22 %  | ISC         | SVG, low-level  | yes     | Foundational; powers many higher-level libs. Steep curve.            |
| **ECharts (Apache)** | ~15 %  | Apache 2.0  | Canvas/SVG      | yes     | Massive in Asia, increasingly global; very feature-complete.         |
| **Plotly.js**        |  ~9 %  | MIT         | WebGL/SVG       | yes     | Same library Python Plotly wraps. Strong scientific feature-set.     |
| **Highcharts**       |  ~8 %  | Commercial  | SVG             | yes     | Industry standard in finance/news. Paid for commercial use.          |
| **Recharts**         |  ~6 %  | MIT         | React-only      | yes     | Default chart lib for React projects.                                |
| **ApexCharts**       |  ~4 %  | MIT         | SVG             | yes     | Popular in admin templates / dashboards.                             |
| **Observable Plot**  |  ~3 %  | ISC         | SVG, declarative| yes     | Mike Bostock's modern successor concept to D3 for everyday charts.   |
| **Vega / Vega-Lite** |  ~3 %  | BSD         | JSON spec       | yes     | Altair already covers Vega-Lite from Python.                         |
| Nivo, Visx, amCharts |  ~4 %  | mixed       | various         | yes     | React/enterprise niches.                                             |

---

## 4. R candidates

| Library         | Share within R | Notes                                                       |
|-----------------|---------------:|-------------------------------------------------------------|
| **ggplot2**     |          ~70 % | The de-facto standard. R-native target #1.                  |
| plotly (R)      |          ~10 % | Wrapper around plotly.js — covered by JS Plotly.            |
| lattice         |           ~8 % | Older base-R style; declining.                              |
| highcharter     |           ~3 % | Wrapper around Highcharts — covered by JS Highcharts.       |
| ggvis, others   |           ~9 % | Long tail.                                                  |

**Take-away:** for R, only **ggplot2** is worth a dedicated entry. Every other
notable R library is a wrapper for a JS library already in scope.

---

## 5. Other languages — informational

| Language | Best library     | Share within language | Worth adding?                                       |
|----------|------------------|----------------------:|-----------------------------------------------------|
| Julia    | **Makie.jl**     | ~45 %                 | Later — once JS + R + ggplot2 land.                 |
| Julia    | Plots.jl         | ~40 %                 | Alternative to Makie; pick one.                     |
| Kotlin   | **lets-plot**    | ~80 %                 | Already in Python; could add native Kotlin entry.   |
| C# /.NET | ScottPlot        | ~50 %                 | Niche; defer.                                       |
| Java     | XChart / JFreeChart | mixed             | Defer.                                              |
| Go       | go-echarts       | n/a                   | Defer.                                              |

---

## 6. The "cross-language library" rule

A library that exists in many languages appears **exactly once**, under the
**most-used variant**. "Most-used" is decided quantitatively:

> A binding qualifies as the canonical entry if it has **≥ 3× more weekly
> downloads** than every other variant. Otherwise default to the native
> implementation.

This avoids subjective per-library debates and makes future calls reproducible.

### JavaScript and TypeScript count as one language

JS and TS are not treated as separate "languages" in the registry. Reasoning:

- TypeScript is a strict superset of JavaScript at the syntax level — every
  valid JS snippet is valid TS.
- The library APIs are identical; types live in separate `.d.ts` files
  shipped alongside the library.
- Charting snippets rarely use TS-only features (generics on D3 selections,
  `satisfies` on option objects, typed React props). The same snippet covers
  both audiences.

**Authoring convention:** ship snippets as plain JavaScript (lowest common
denominator). Exception: libraries that are only meaningfully shown in a
typed/JSX form in the wild (e.g. **Recharts**) are written as TSX.

### React and other UI frameworks count as JavaScript too

React is a JavaScript library, not a language. JSX/TSX compiles to plain JS
function calls. Same applies to Vue (`vue-chartjs`), Svelte (`layercake`),
Angular (`ngx-charts`).

The framework requirement is a **runtime constraint**, not a language. Model
it on the library metadata, not on `language_id`:

```python
# Suggested addition to LIBRARIES_METADATA
{
    "id": "recharts",
    "language_id": "javascript",
    "framework": "react",   # one of: none, react, vue, svelte, angular
    ...
}
```

Benefits:
- One language entry (JavaScript) covers Chart.js *and* Recharts.
- Frontend can offer dual filters: "all JavaScript libs" and "React-compatible".
- SEO indexes Recharts under both *"javascript chart library"* and
  *"react chart library"* without duplicating the registry.
- The same field generalises later to Vue/Svelte/Angular if those become
  relevant — no schema change needed.

Framework-agnostic libraries set `framework: "none"` (the default).
Framework-only libraries get tagged accordingly. **Recharts** is the only
Tier 3 entry currently affected; everything in Tier 1 / Tier 2 is
framework-agnostic.

### Licensing policy

anyplot prioritises **FOSS-licensed** libraries (MIT, BSD, Apache, ISC, GPL).
Commercial libraries with a **free-for-private-use** tier — Highcharts,
amCharts — are allowed in the catalogue but de-emphasised:

- They must never displace a comparable FOSS alternative in a higher tier.
- Each entry must clearly mark its license and link to the upstream license
  page. Suggested metadata field on each library:

  ```python
  "license": "MIT" | "Apache-2.0" | "BSD-3-Clause" | "ISC" | "GPL-2.0"
           | "Commercial (free for non-commercial use)"
  ```

- The frontend should expose a "FOSS only" filter so users who need
  permissive licensing can exclude commercial entries with one click.

Hard-paywalled libraries with no free tier (e.g. amCharts 4 Enterprise without
the personal licence, FusionCharts) are out of scope.

Applied to every cross-language library in or near scope:

| Library             | Native     | Most-used variant      | Canonical entry           | Action vs current state                          |
|---------------------|------------|------------------------|---------------------------|--------------------------------------------------|
| Plotly              | JavaScript | Python (~22× JS)       | **Python**                | Keep as is. No separate JS entry.                |
| Highcharts          | JavaScript | JavaScript (~200× Py)  | **JavaScript**            | Replace current Python entry with JS.            |
| Vega-Lite           | JSON spec  | Python (Altair)        | **Altair (Python)**       | Keep as is. Skip a separate Vega entry.          |
| ggplot2 vs plotnine | R / Python | R for ggplot2          | **Both** (sister libs)    | Add ggplot2 as R entry; keep plotnine in Python. |
| lets-plot           | Kotlin     | Python                 | **Python**                | Keep as is.                                      |
| ECharts             | JavaScript | JavaScript             | **JavaScript**            | Add as new JS entry.                             |
| Chart.js, D3, etc.  | JavaScript | JavaScript             | **JavaScript**            | Add as new JS entries.                           |

Net effect on the existing catalogue: **only Highcharts moves.** Plotly and
lets-plot stay where they are because their Python variants outweigh the
native versions by more than the 3× threshold.

---

## 7. Recommended priority order

Ranked by `reach × ease-of-integration ÷ duplication-risk`.

### Tier 1 — do first (biggest reach, cleanest fit)

1. **Chart.js (JavaScript)** — largest JS audience, smallest API surface, easy
   to render to PNG via headless browser. The single highest-ROI addition.
2. **D3.js (JavaScript)** — expected by any serious charting site; SEO magnet
   ("d3 example" is one of the most-searched dataviz queries).
3. **ECharts (JavaScript)** — broad coverage of chart types, Apache-licensed,
   complements Chart.js (heavyweight vs. lightweight).

### Tier 2 — high value, slightly more work

4. **ggplot2 (R)** — MIT/GPL-2. Unlocks the entire R / academic audience;
   first non-Python language, so it also validates the multi-language
   pipeline on a non-JS runtime.
5. **Highcharts (JavaScript)** — *Commercial, free for non-commercial use.*
   Replaces the current Python Highcharts entry; the JS variant outweighs the
   Python wrapper by ~200×, so the most-used rule mandates the move. Tag with
   the commercial-license flag and surface the licence prominently on the
   plot pages.

### Tier 3 — opportunistic, ecosystem-specific

6. **Recharts (TypeScript / React)** — captures the React niche, which is
   large but framework-locked.
7. **Observable Plot (JavaScript)** — small but trendy; cheap once D3 is in.
8. **Makie.jl (Julia)** — first Julia entry once the multi-language pipeline
   is mature.
9. **ApexCharts (JavaScript)** — fills the "admin-template / dashboard" SEO
   long tail.

### Defer / skip

- **plotly.js (JavaScript)** — Python is the most-used Plotly variant by ~22×,
  so the rule says one entry only, in Python.
- **plotly (R)**, **highcharter (R)**, **plotly (Julia)** — wrappers around
  libraries already covered under their most-used variant.
- **MATLAB**, **Java/Swing**, **C# WinForms** — declining or niche.
- **Vega / Vega-Lite as a separate entry** — already covered via Altair.

---

## 8. Suggested phased rollout

| Phase | Adds                                | New languages | Cumulative library count |
|-------|-------------------------------------|---------------|--------------------------|
| 0 (today) | —                               | Python        |  9                       |
| 1     | Chart.js, D3.js, ECharts            | + JavaScript  | 12                       |
| 2     | Highcharts (replaces Python entry)  | —             | 12                       |
| 3     | ggplot2                             | + R           | 13                       |
| 4     | Recharts, Observable Plot           | —             | 15                       |
| 5     | Makie.jl, ApexCharts                | + Julia       | 17                       |

After Phase 3 anyplot covers ~95 % of global charting-library demand with 13
entries.

---

## 9. Settled decisions

- **JS / TS treated as one language**, snippets authored in plain JS (TSX
  only when a library is realistically only used that way, e.g. Recharts).
- **React / Vue / Svelte / Angular** are JavaScript with a `framework`
  metadata flag, not separate languages.
- **Cross-language libraries** appear once, under the variant with ≥ 3× more
  weekly downloads (else native).
- **Highcharts** moves from Python to JavaScript. Keep both entries for one
  release as a deprecation window, then drop the Python entry.
- **Licensing**: FOSS-first; libraries with a free-for-private-use tier
  (Highcharts, amCharts) are allowed but tagged and never crowd out FOSS
  alternatives at the same tier.
- **Annual review cadence.** Once a year, revisit this document and check:
  1. **Downloads**: re-run the 3× test on every cross-language library; flip
     canonical variants where the gap has reversed.
  2. **Visitor data** (Plausible): which libraries / plot pages drew the most
     traffic? Promote rising entries in the recommendation tiers; demote ones
     nobody visits.
  3. **Trend scan**: JS Rising Stars, PyPI top-movers, GitHub Trending in
     `data-visualization`. Add anything that has clearly broken into the
     mainstream and isn't already covered.
  4. **Tier reshuffle**: update §7 priority order accordingly.

  An off-cycle review is also triggered by a major release of an in-scope
  library or a clear emerging contender.

## 10. Open questions for the team

1. **amCharts inclusion.** Same licence model as Highcharts. Add as a Tier 3
   entry, or skip on the grounds that Highcharts already covers the
   "commercial, free for private" niche?
