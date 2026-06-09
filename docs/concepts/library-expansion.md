# Library Expansion Roadmap

Strategic overview for expanding anyplot beyond Python into a true multi-language
gallery. This document estimates the global market for charting libraries,
ranks candidates by reach and integration cost, and recommends a concrete
priority order.

> **Note on numbers.** The percentages below are *estimates* synthesized from
> public signals (Stack Overflow Developer Survey, PyPI/npm download counts,
> GitHub stars, Google Trends, JS Rising Stars). They are good enough to
> prioritize — they are not authoritative market shares.

---

## 1. Current state

anyplot currently ships **8 Python libraries**, **1 R library** (ggplot2 —
the first non-Python entry; landed as Phase 3), **1 Julia library** (Makie.jl
via CairoMakie; landed as Phase 5 ahead of the original roadmap order — see §8),
and **5 JavaScript libraries** (Chart.js / D3 / ECharts from Phase 1, Highcharts
migrated in Phase 2, and MUI X — a React entry — pulled forward in Phase 4).
That is **15 libraries** across four languages.

| #  | Library    | Native     | In anyplot as | Most-used variant | Notes                                       |
|----|------------|------------|---------------|-------------------|---------------------------------------------|
| 1  | Matplotlib | Python     | Python        | Python            | Native = most-used.                         |
| 2  | Seaborn    | Python     | Python        | Python            | Built on matplotlib.                        |
| 3  | Plotly     | JavaScript | Python        | **Python**        | PyPI ~18 M / wk vs `plotly.js` ~0.8 M / wk. |
| 4  | Bokeh      | Python     | Python        | Python            | Native = most-used.                         |
| 5  | Altair     | Python     | Python        | Python            | Python interface to Vega-Lite (JSON spec).  |
| 6  | plotnine   | Python     | Python        | Python            | Sister library to ggplot2, not a wrapper.   |
| 7  | Pygal      | Python     | Python        | Python            | Native = most-used.                         |
| 8  | Highcharts | JavaScript | Python        | **JavaScript**    | npm ~1 M / wk vs `highcharts-core` ~5 k / wk.|
| 9  | lets-plot  | Kotlin     | Python        | Python            | Python frontend has the most users today.   |
| 10 | ggplot2    | R          | R             | R                 | First non-Python entry; landed in Phase 3.  |
| 11 | Makie.jl   | Julia      | Julia         | Julia             | CairoMakie backend (static PNG). Phase 5.   |
| 12 | MUI X Charts | JavaScript | JavaScript  | JavaScript        | React framework (`framework: react`), `.tsx`. Community `@mui/x-charts` (MIT) only; Pro/Premium out of scope. First React entry — Phase 4, pulled forward (§8). |

(Chart.js, D3, ECharts also ship as native JavaScript entries from Phase 1 —
they are framework-agnostic and omitted from this cross-language table since
there is no "most-used variant" question for them.)

**Implication:** under the most-used rule (see §6), only **Highcharts** was
filed under the wrong language and moved to JavaScript (Phase 2). Plotly and
lets-plot are correctly filed as Python despite not being native. **MUI X** is
native JavaScript and the React variant is the only one, so it files as
JavaScript with a `framework: react` flag.

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
| **MUI X Charts**     |  ~2 %  | MIT †       | React (SVG)     | yes     | Charts in the MUI ecosystem. Community pkg `@mui/x-charts` is MIT; Pro features (zoom/pan, …) are commercial → out of scope. |
| Nivo, Visx, amCharts |  ~4 %  | mixed       | various         | yes     | React/enterprise niches.                                             |

† MIT applies to the community package `@mui/x-charts`. `@mui/x-charts-pro` (advanced
zoom & pan, etc.) is commercially licensed and out of scope — see §9.

---

## 4. R candidates

| Library         | Share within R | Notes                                                       |
|-----------------|---------------:|-------------------------------------------------------------|
| **ggplot2**     |          ~70 % | The de facto standard. R-native target #1.                  |
| plotly (R)      |          ~10 % | Wrapper around plotly.js — covered by JS Plotly.            |
| lattice         |           ~8 % | Older base-R style; declining.                              |
| highcharter     |           ~3 % | Wrapper around Highcharts — covered by JS Highcharts.       |
| ggvis, others   |           ~9 % | Long tail.                                                  |

**Take-away:** for R, only **ggplot2** is worth a dedicated entry. Every other
notable R library is a wrapper for a JS library already in scope.

---

## 5. Other languages — informational

After Python, R, and JavaScript, the marginal value of each additional
language drops sharply. Most devs in other languages render web charts via
JavaScript anyway (a Go backend ships JSON to a Chart.js frontend; a Java
service does the same). Only one language — **Julia** — has a clear case
for a dedicated entry; the rest are long tail.

### Scope criteria for any new language

A language qualifies for a dedicated entry only if it satisfies all three:

1. **Code-driven** — plots are produced from a pure source-code snippet
   (no GUI / click workflows).
2. **Free toolchain** — a FOSS interpreter/compiler exists so CI can render
   previews and contributors can participate without license costs.
3. **Public package registry** — libraries install from an open registry
   (PyPI, npm, CRAN, `Pkg.jl`, …).

### Candidate ranking

| Language | Best library         | Share within language | Verdict                                             |
|----------|----------------------|----------------------:|-----------------------------------------------------|
| Julia    | **Makie.jl**         | ~45 %                 | **Phase 5.** Distinct scientific stack; not a wrapper.|
| Julia    | Plots.jl             | ~40 %                 | Alternative; pick Makie unless visitor data flips.   |
| Swift    | Swift Charts         | ~70 %                 | Optional Phase 6 if Apple-platform audience matters. |
| Kotlin   | lets-plot (Kotlin)   | ~80 %                 | Defer; covered today via the Python lets-plot entry. |
| C# /.NET | ScottPlot            | ~50 %                 | Defer; mostly Desktop/WinForms, weak web fit.        |
| Java     | XChart / JFreeChart  | mixed                 | Skip; Java services use JS for web output.           |
| Go       | go-echarts           | n/a                   | Skip; ECharts wrapper, already covered in JS.        |
| Rust     | plotters             | n/a                   | Skip; tiny absolute volume.                          |
| F# / Scala | XPlot / Vegas      | n/a                   | Skip; Plotly/Vega wrappers, already covered.         |

### Explicitly out of scope

These fail at least one of the scope criteria above and should not be
revisited unless the criteria themselves change.

| Tool / language               | Failed criterion              | Reason                                        |
|-------------------------------|-------------------------------|-----------------------------------------------|
| **Excel, Google Sheets, Numbers** | Code-driven                | Charts are GUI-clicked; no source-code form.  |
| **Tableau, Power BI, Looker, Qlik** | Code-driven              | BI dashboards, not code snippets.             |
| **MATLAB**                    | Free toolchain                | Paid license, closed ecosystem, declining.    |
| **SAS, SPSS, Stata**          | Free toolchain + Code-driven  | Paid + mostly GUI-driven.                     |
| **Mathematica / Wolfram**     | Free toolchain                | Paid license, niche.                          |
| **Origin, SigmaPlot, Prism**  | Free toolchain + Code-driven  | Paid scientific GUIs.                         |

---

## 6. The "cross-language library" rule

In steady state, a library that exists in many languages appears **exactly
once**, under the **most-used variant**. "Most-used" is decided
quantitatively:

> A binding qualifies as the canonical entry if it has **≥ 3× more weekly
> downloads** than every other variant. Otherwise default to the native
> implementation.

This avoids subjective per-library debates and makes future calls reproducible.

**Exception — deprecation window.** When a library moves from one language
to another (see Highcharts in §9), both entries may co-exist for one release
cycle so existing links don't break. After that release the superseded entry
is removed and the steady-state "exactly once" rule applies again.

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
Framework-only libraries get tagged accordingly. **Recharts** and **MUI X
Charts** are the Tier 3 entries currently affected; everything in Tier 1 /
Tier 2 is framework-agnostic.

### Licensing policy

anyplot prioritizes **FOSS-licensed** libraries (MIT, BSD, Apache, ISC, GPL).
Commercial libraries with a **free-for-private-use** tier — Highcharts,
amCharts — are allowed in the catalogue but de-emphasized:

- They must never displace a comparable FOSS alternative in a higher tier.
- Each entry must clearly mark its license and link to the upstream license
  page. Use **valid SPDX identifiers** so the field stays machine-readable;
  add a free-text note for non-SPDX cases:

  ```python
  # SPDX identifiers (preferred):
  "license": "MIT" | "Apache-2.0" | "BSD-3-Clause" | "ISC"
           | "GPL-2.0-only" | "GPL-2.0-or-later" | "GPL-3.0-or-later"

  # Non-SPDX (commercial with free private-use tier):
  "license": "LicenseRef-Commercial-Free-NonCommercial"
  ```

- The frontend should expose a "FOSS only" filter so users who need
  permissive licensing can exclude commercial entries with one click.

Hard-paywalled libraries with no free tier (e.g. amCharts 4 Enterprise without
the personal license, FusionCharts) are out of scope.

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

4. **ggplot2 (R)** — MIT (per current CRAN DESCRIPTION). Unlocks the entire
   R / academic audience; first non-Python language, so it also validates the
   multi-language pipeline on a non-JS runtime.
5. **Highcharts (JavaScript)** — *Commercial, free for non-commercial use.*
   Replaces the current Python Highcharts entry; the JS variant outweighs the
   Python wrapper by ~200×, so the most-used rule mandates the move. Tag with
   the commercial-license flag and surface the license prominently on the
   plot pages.

### Tier 3 — opportunistic, ecosystem-specific

6. **Recharts (TypeScript / React)** — captures the React niche, which is
   large but framework-locked.
7. **Observable Plot (JavaScript)** — small but trendy; cheap once D3 is in.
8. **Makie.jl (Julia)** — first Julia entry once the multi-language pipeline
   is mature.
9. **ApexCharts (JavaScript)** — fills the "admin-template / dashboard" SEO
   long tail.
10. **MUI X Charts (TypeScript / React)** — community `@mui/x-charts` (MIT) serves the
    MUI/React dashboard audience; **Pro features stay out** (see §9). Framework-locked
    like Recharts, so it sits in the same niche tier.

### Defer / skip

- **plotly.js (JavaScript)** — Python is the most-used Plotly variant by ~22×,
  so the rule says one entry only, in Python.
- **plotly (R)**, **highcharter (R)**, **plotly (Julia)** — wrappers around
  libraries already covered under their most-used variant.
- **MATLAB**, **Java/Swing**, **C# WinForms** — declining or niche.
- **Vega / Vega-Lite as a separate entry** — already covered via Altair.

---

## 8. Suggested phased rollout

| Phase | Adds                                | New languages | Cumulative library count | Status   |
|-------|-------------------------------------|---------------|--------------------------|----------|
| 0     | —                                   | Python        |  9                       | shipped  |
| 1     | Chart.js, D3.js, ECharts            | + JavaScript  | 14                       | **in progress** — JS runtime (Node 22 + Playwright render harness), registry, workflows, prompts, and frontend landed; plot implementations generated next via `bulk-generate`. Cumulative count is 14 (the Phase-3/5 R+Julia entries already shipped). |
| 2     | Highcharts (replaces Python entry)  | —             | 14                       | **shipped** (#8242) — Highcharts migrated Python → JavaScript. Executed as a **clean break** (the §6 deprecation-window *fallback*, chosen by the owner for simplicity): the 322 Python `highcharts.py` impls were removed and the canonical entry flipped to the native `highcharts.js` (v12.6.0) on the Node + Playwright harness; JS implementations are recreated gradually via `bulk-generate` / `daily-regen`. Cumulative count stays 14 — a move, not an addition. |
| 3     | **ggplot2**                         | **+ R**       | **10**                   | **shipped** (Phase 3 was implemented before Phases 1+2; net total was 10 until Phase 5 landed Julia) |
| 4     | **MUI X Charts** (Recharts, Observable Plot deferred) | — | 15 | **MUI X shipped** — its Tier-3 React entry (§7 #10) was **pulled forward** as the JavaScript rollout's third issue (after Phase 1 runtime + Phase 2 Highcharts) to validate the **React/TSX harness path** end to end. Community `@mui/x-charts` (MIT) only; rendered through the harness's esbuild `framework: react` branch. Cumulative count 15 (a genuine addition). Recharts / Observable Plot remain planned. |
| 5     | **Makie.jl** (ApexCharts deferred)  | **+ Julia**   | **11**                   | **shipped** (Phase 5 was implemented before Phases 1+2+4 to validate the multi-language pipeline on a second non-Python runtime; ApexCharts split to a later phase) |

> **Why Phase 2 ≠ Tier 2 #4 from §7.** §7 ranks ggplot2 (Tier 2 #4) above
> Highcharts (Tier 2 #5) by reach; §8 still ships Highcharts first because
> it reuses the JavaScript pipeline stood up in Phase 1, whereas ggplot2
> requires a brand-new R runtime in CI. Pipeline cost dominates here, so
> Highcharts is cheaper to ship next even though it ranks lower on raw
> reach.

With Phases 1–5 landed (plus MUI X pulled forward from Phase 4), anyplot covers
~95 % of global charting-library demand with **15 entries** across Python, R,
Julia, and JavaScript.

---

## 9. Settled decisions

- **JS / TS treated as one language**, snippets authored in plain JS (TSX
  only when a library is realistically only used that way, e.g. Recharts).
- **React / Vue / Svelte / Angular** are JavaScript with a `framework`
  metadata flag, not separate languages.
- **Cross-language libraries** appear once, under the variant with ≥ 3× more
  weekly downloads (else native).
- **Highcharts** moved from Python to JavaScript (Phase 2, #8242). The §6
  deprecation window was one option; in practice it shipped as a **clean break**
  (the documented fallback) — the Python `highcharts-core` impls were dropped and
  the canonical entry flipped straight to the native `highcharts.js`, with JS
  implementations recreated gradually rather than dual-serving Python + JS for one
  release. Old `/{spec}/python/highcharts` deep links fall back to the spec hub.
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
- **amCharts: skipped.** Duplicates the Highcharts slot (same
  commercial-with-free-tier model) at ~18× lower download volume, and a
  second commercial entry would weaken the FOSS-first stance. Revisit only
  if Plausible data shows unmet demand for amCharts-specific examples.
- **MUI X Charts: community tier only.** `@mui/x-charts` (MIT) is in scope as a
  React/JavaScript entry (Tier 3, §7). `@mui/x-charts-pro` / Premium features (advanced
  zoom & pan, etc.) are commercially licensed and out of scope — same FOSS-first reasoning
  as the Highcharts/amCharts policy in §6. Snippets must use only the MIT community surface;
  only the community package is installed, so a Pro import fails the build outright.
- **MUI X renders through the harness's React (esbuild) branch.** MUI X is the
  catalog's first `framework: react` and first `.tsx` entry, so it does **not**
  use the UMD-global path of the other JS libs. Its snippet is a `.tsx` module
  that **default-exports a React component**; the Node + Playwright render harness
  esbuild-bundles it with `react` / `react-dom` / `@mui/x-charts`, wraps it in a
  theme-aware MUI `ThemeProvider` (mapped onto `ANYPLOT_TOKENS`), mounts it with
  `createRoot`, and screenshots `#container` at the canonical canvas size — the
  same exact-pixel contract as the framework-agnostic libs. The browser (not jsdom
  SSR) is required because MUI X measures real SVG text (getBBox) for axis/legend
  layout. `language_id` stays `javascript`; React is a runtime constraint, not a
  language (§6).
- **Phase 5 (Julia / Makie.jl) shipped before Phases 1+2 (JavaScript).**
  The original roadmap order was Phase 1 (Chart.js / D3 / ECharts) →
  Phase 2 (Highcharts JS) → Phase 3 (ggplot2) → Phase 4 (Recharts /
  Observable Plot) → Phase 5 (Makie.jl). After Phase 3 landed and the
  multi-language pipeline proved stable on R, shipping Julia next provided
  a cheap second non-Python validation that surfaces multi-language gaps
  the JS work would otherwise hit cold. The JavaScript phases remain
  planned; their relative ordering is unchanged.
- **Makie.jl over Plots.jl.** Makie is a distinct scientific stack, not a
  wrapper, and it earns its own entry under the "most-used variant" rule
  in §6. Plots.jl is the alternative; we ship Makie unless Plausible data
  later shows the audience flips. `PlotlyJS.jl` is a wrapper around
  plotly.js and is already covered via the Python Plotly entry.
- **CairoMakie backend only.** GLMakie / WGLMakie are interactive backends
  out of scope for the static gallery; `INTERACTIVE_LIBRARIES` intentionally
  excludes Makie.

## 10. Open questions for the team

None — all design decisions are recorded in §9. New questions surface
through the annual review described above.
