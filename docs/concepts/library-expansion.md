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

| # | Library    | Native language | In anyplot as | Notes                                            |
|---|------------|-----------------|---------------|--------------------------------------------------|
| 1 | Matplotlib | Python          | Python        | True native.                                     |
| 2 | Seaborn    | Python          | Python        | Built on matplotlib.                             |
| 3 | Plotly     | JavaScript      | Python        | Python is a wrapper around `plotly.js`.          |
| 4 | Bokeh      | Python          | Python        | True native.                                     |
| 5 | Altair     | Python          | Python        | Python interface to Vega-Lite (JSON spec).       |
| 6 | plotnine   | Python          | Python        | Python port of R's `ggplot2`.                    |
| 7 | Pygal      | Python          | Python        | True native.                                     |
| 8 | Highcharts | JavaScript      | Python        | Python is a paid wrapper; native is JS.          |
| 9 | lets-plot  | Kotlin          | Python        | Kotlin/JVM core; Python is one of the front-ends.|

**Implication:** three of the nine entries (Plotly, Highcharts, lets-plot) are
already non-native bindings. Following the "native / most-used variant only"
rule strictly would move them to their native languages once those land.

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

Your stated rule: a library that exists in many languages should appear once,
in its **native or most-used** variant. Apply it concretely:

| Library             | Native     | Most-used variant   | Recommended single entry            | Action vs current state                          |
|---------------------|------------|---------------------|-------------------------------------|--------------------------------------------------|
| Plotly              | JavaScript | Python (by volume)  | **Both** — JS for web, Python for DS| Keep Python; add `plotly.js` as new JS entry.    |
| Highcharts          | JavaScript | JavaScript          | **JavaScript only**                 | Replace current Python entry with JS native.     |
| Vega-Lite           | JSON spec  | Python (Altair)     | **Altair (Python)**                 | Keep as is. Skip a separate Vega entry.          |
| ggplot2 / plotnine  | R          | R                   | **ggplot2 (R)**, keep plotnine      | plotnine is a port, not a wrapper — both fine.   |
| lets-plot           | Kotlin     | Python              | **Python** (or add Kotlin later)    | Keep Python; consider Kotlin once JVM matters.   |
| ECharts             | JavaScript | JavaScript          | **JavaScript only**                 | Add as new JS entry.                             |
| Chart.js, D3, etc.  | JavaScript | JavaScript          | **JavaScript only**                 | Add as new JS entries.                           |

The two clear "fix the existing entry" decisions: **Highcharts** should move to
JS, and **Plotly** should *also* gain a JS entry (the Python entry is justified
by sheer Python-side usage, but the native target is `plotly.js`).

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

4. **ggplot2 (R)** — unlocks the entire R / academic audience; first
   non-Python language so you also validate the multi-language pipeline on a
   non-JS runtime.
5. **Plotly.js (JavaScript)** — native sibling of the existing Python entry;
   reuses spec knowledge.
6. **Highcharts (JavaScript)** — *replaces* the current Python Highcharts
   entry. Keeps the brand, fixes the "native variant" rule, and the JS API is
   the canonical one developers search for.

### Tier 3 — opportunistic, ecosystem-specific

7. **Recharts (TypeScript / React)** — captures the React niche, which is
   large but framework-locked.
8. **Observable Plot (JavaScript)** — small but trendy; cheap once D3 is in.
9. **Makie.jl (Julia)** — first Julia entry once the multi-language pipeline
   is mature.
10. **ApexCharts (JavaScript)** — fills the "admin-template / dashboard" SEO
    long tail.

### Defer / skip

- **plotly (R)**, **highcharter (R)**, **plotly (Julia)** — wrappers; already
  covered by the JS native entries.
- **MATLAB**, **Java/Swing**, **C# WinForms** — declining or niche.
- **Vega / Vega-Lite as a separate entry** — already covered via Altair.

---

## 8. Suggested phased rollout

| Phase | Adds                                | New languages | Cumulative library count |
|-------|-------------------------------------|---------------|--------------------------|
| 0 (today) | —                               | Python        |  9                       |
| 1     | Chart.js, D3.js, ECharts            | + JavaScript  | 12                       |
| 2     | Plotly.js, Highcharts (replaces py) | —             | 13                       |
| 3     | ggplot2                             | + R           | 14                       |
| 4     | Recharts, Observable Plot           | —             | 16                       |
| 5     | Makie.jl, ApexCharts                | + Julia       | 18                       |

After Phase 3 anyplot covers ~95 % of global charting-library demand with 14
entries.

---

## 9. Open questions for the team

1. **Highcharts migration.** Do we replace the existing Python entry or keep
   both during a deprecation window? (Recommend: keep both for one release,
   then remove the Python entry.)
2. **React-specific libraries.** Recharts, Visx, Nivo only make sense if
   anyplot intends to support framework-specific entries. If we keep entries
   framework-agnostic, drop them and lean on Chart.js / ECharts.
3. **TypeScript vs JavaScript.** Treat as one language with TS as the default
   source form, or as two separate "languages" in the registry? (Recommend:
   one — the file extension and tooling differ, but the library identity does
   not.)
4. **Commercial licenses.** Highcharts requires a paid licence for commercial
   use. Confirm the project's stance on showcasing it before generating
   examples.
