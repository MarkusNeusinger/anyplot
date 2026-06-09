# Highcharts

Highcharts is the industry-standard JavaScript charting library for finance,
news, and BI dashboards (SVG-rendered, enormously flexible). As of Phase 2 of
the JavaScript rollout, anyplot's canonical `highcharts` entry is the **native
JavaScript** library — the file extension is **`.js`** and the runtime is the
**browser render harness** (`node automation/js-render/render.mjs`), **not**
Python (`highcharts-core`), Rscript, or julia.

> **Commercial license — keep it visible.** Highcharts is free for personal /
> non-commercial use but requires a paid license for commercial use
> (https://www.highcharts.com/license). Keep the `// License:` line in the
> header block (below) so it ships in every generated snippet. Do not strip the
> Highcharts credit for a license you don't hold.

Highcharts charts render in a browser DOM — there is no headless CLI that writes
a PNG. You author an **idiomatic Highcharts snippet** that draws into the mount
node `#container`; the harness wraps it in an HTML page, loads the pinned
`highcharts` bundle, renders it under headless Chromium (Playwright), and
screenshots the mount node at the exact canvas size. It emits **both**
`plot-{theme}.png` and `plot-{theme}.html`. You never write to the filesystem,
build HTML, or drive a screenshot — the harness owns all of that.

## IMPORTANT: No Workarounds

**If Highcharts cannot implement a plot type natively, DO NOT shell out to
Chart.js, D3, ECharts, or any other library.** Highcharts has a large built-in
catalog (line, spline, area, column/bar, scatter, bubble, pie, gauge, heatmap,
treemap, sunburst, sankey, dependency-wheel, networkgraph, funnel, …). If the
spec's core value is genuine interactivity (hover/zoom/drilldown) with no static
form, return `NOT_FEASIBLE`. Do not simulate interaction.

Only the **core `highcharts` bundle** is vendored — the `Highcharts` global is
the single global available. Do **not** rely on `highcharts-more` (bubble,
polar, gauge, boxplot, errorbar, columnrange), `modules/*` (treemap, sunburst,
sankey, networkgraph, heatmap, …), or `highcharts-3d`: they are **not loaded**.
If a spec needs a series type that lives in one of those add-on modules, return
`NOT_FEASIBLE` rather than `import`ing it (there is no import — see Forbidden).

## The mount-node contract (how your snippet connects to the harness)

The harness gives you a pre-sized `<div id="container">` and these globals (the
browser has no `process.env`, so this is the JS analogue of `ANYPLOT_THEME`):

```js
window.ANYPLOT_THEME      // "light" | "dark"
window.ANYPLOT_TOKENS     // { pageBg, elevatedBg, ink, inkSoft, grid, palette[8], amber, seq[2], div[3] }
window.ANYPLOT_SIZE       // { width, height } — the CSS mount size
window.Highcharts         // the Highcharts global (already loaded)
```

Your snippet must:

1. Call `Highcharts.chart("container", option)` (string id of the mount node).
2. Set `chart.animation: false` and `plotOptions.series.animation: false` so the
   screenshot never catches a mid-animation frame.

Do **not** pass an explicit `chart.width` / `chart.height` — Highcharts auto-sizes
to `#container`, which the harness has already sized to the canonical canvas. The
exact pixels come from Playwright `deviceScaleFactor: 2` over that fixed mount, so
you only pick the orientation.

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (the `impl-review.yml`
gate rejects anything off by more than 16 px and re-triggers repair):

| Orientation | Pixels      | How                                             |
|-------------|-------------|-------------------------------------------------|
| Landscape   | 3200 × 1800 | default                                         |
| Square      | 2400 × 2400 | add directive `//# anyplot-orientation: square` |

The harness produces these exactly (1600×900 / 1200×1200 CSS × `deviceScaleFactor 2`);
Highcharts fills the mount. For a square spec (pie / gauge / radial / heatmap),
put this on its own line near the top:

```js
//# anyplot-orientation: square
```

## Sizing — CSS px in the mount's coordinate space (NOT native 3200 px)

The mount is **1600×900** (landscape) / **1200×1200** (square) CSS px; the 2×
device scale is what lands the PNG on 3200×1800 / 2400×2400. So size fonts and
markers in that CSS space — small numbers, like the other JS libs — **not** the
old Python native-pixel values (66 px / 56 px / 44 px were for headless-Chrome at
dpr=1 and are wrong here). Good starting values: title `~22px`, axis titles
`~16px`, tick/legend labels `~14px`, scatter `marker.radius ~5`, `line.lineWidth ~2.5`.

## Reproducibility

Generate data in-memory and deterministically. There is no seeded RNG in the
browser; use a tiny fixed-seed LCG or hard-code the data. **Never `fetch()` or
load from a CDN/network** — the runtime is offline and the HTML must be
self-contained.

## Colors — Imprint palette (from `window.ANYPLOT_TOKENS`)

The first categorical series is **always** `#009E73` (`tokens.palette[0]`). Set
Highcharts' top-level `colors` array to the Imprint palette. Data colors are
**identical** between light and dark — only chrome flips.

```js
const t = window.ANYPLOT_TOKENS;
option.colors = t.palette;                 // categorical cycle, first = brand green
// continuous (heatmap / treemap colorAxis) — build from the Imprint stops:
option.colorAxis = { stops: [[0, t.seq[0]], [1, t.seq[1]]] };          // sequential
// diverging (meaningful midpoint):
option.colorAxis = { stops: [[0, t.div[0]], [0.5, t.div[1]], [1, t.div[2]]] };
```

Never use Highcharts' default palette or named gradients (viridis / rainbow).

## Theme-adaptive chrome (Highcharts mapping)

Map tokens onto the chart chrome. The `#container` background is already
`t.pageBg`, so set `chart.backgroundColor: "transparent"` (the page shows
through) — **never white**. Always disable the credits watermark.

```js
const t = window.ANYPLOT_TOKENS;
Highcharts.chart("container", {
  chart: { type: "column", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title:    { text: "spec-id · javascript · highcharts · anyplot.ai",
              style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  subtitle: { style: { color: t.inkSoft, fontSize: "14px" } },
  xAxis: { lineColor: t.inkSoft, tickColor: t.inkSoft, gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } },
           title:  { style: { color: t.inkSoft, fontSize: "16px" } } },
  yAxis: { lineColor: t.inkSoft, tickColor: t.inkSoft, gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } },
           title:  { style: { color: t.inkSoft, fontSize: "16px" } } },
  legend: { itemStyle: { color: t.inkSoft, fontSize: "14px" },
            itemHoverStyle: { color: t.ink } },
  plotOptions: { series: { animation: false } },
  series: [/* … */],
});
```

Pie / gauge / sunburst have no `xAxis`/`yAxis` — drop those and style via
`dataLabels` / `plotOptions.{type}` instead. Use `t.ink` for data labels on
light or dark.

## Script Skeleton

```js
//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const categories = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const values = [12, 19, 7, 15, 11];

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "column", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "bar-basic · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  xAxis: { categories,
           lineColor: t.inkSoft, tickColor: t.inkSoft,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } } },
  yAxis: { title: { text: "Value", style: { color: t.inkSoft, fontSize: "16px" } },
           gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } } },
  legend: { enabled: false },
  plotOptions: { series: { animation: false },
                 column: { borderWidth: 0 } },
  series: [{ name: "Visits", data: values, colorByPoint: true }],
});
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/javascript/highcharts.js` —
  rendered twice by the harness with different `ANYPLOT_THEME`.
- Generated artifacts (written by the harness, not the snippet):
  `plot-light.png` + `plot-dark.png` and `plot-light.html` + `plot-dark.html`
  (Highcharts is in `INTERACTIVE_LIBRARIES`).

## Header Style

```js
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-09
```

The `impl-review.yml` header-rewrite replaces the leading `//` block and skips
`//#` directive lines, so the `//# anyplot-orientation:` line survives — keep it
on its own line.

## Forbidden patterns

- **No `highcharts-core`** — that is the deprecated Python wrapper; this entry is
  the native JS library.
- **No `import` / `require` / `<script src=…>`** — `Highcharts` is already a global.
- **No add-on modules** — no `highcharts-more`, `modules/*`, `highcharts-3d`,
  `highcharts-gantt`, `highmaps`; only the core bundle is loaded.
- **No CDN / `fetch` / network** — the runtime is offline and the HTML must be
  self-contained.
- **No inline HTML scaffold or screenshot code** (no Selenium, no `document`
  plumbing) — the harness owns the HTML page and the Playwright screenshot.
- **No white background** and **no Highcharts default palette / named gradients**.

## Highcharts-Specific Gotchas

- **`animation: false` is mandatory** (both `chart.animation` and
  `plotOptions.series.animation`) — otherwise the screenshot catches a
  mid-animation frame.
- Call `Highcharts.chart("container", …)` with **no** explicit `chart.width` /
  `chart.height` — it auto-sizes to the pre-sized mount.
- `credits: { enabled: false }` — drop the highcharts.com watermark.
- Tooltip / drilldown / zoom are interactive-only and won't appear in the static
  PNG; that's expected — don't try to force them open for the screenshot.
- Highcharts renders SVG (the harness's draw check passes on `<svg>`); you may
  set `window.__anyplotReady = true` after the chart call for precise timing, but
  with `animation: false` the harness's fonts-ready + double-rAF settle is enough.
