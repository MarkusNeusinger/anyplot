# Highcharts

Highcharts is the industry-standard JavaScript charting library for finance,
news, and BI dashboards (SVG-rendered, enormously flexible). As of Phase 2 of
the JavaScript rollout, anyplot's canonical `highcharts` entry is the **native
JavaScript** library — the file extension is **`.js`** and the runtime is the
**browser render harness** (`node automation/js-render/render.mjs`), **not**
Python (`highcharts-core`), Rscript, or julia.

**API level:** Highcharts 13. The root `package-lock.json` pins this major;
write against its API.

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

**Computation:** the core bundle has no statistics helpers: the histogram and
bell-curve series live in modules that are not loaded, so hand-written binning,
box statistics and densities are fine. Keep them short.

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
put this on its own line directly below the header block (see "Header Style"):

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

## Data block

The file follows the six zones of `prompts/adaptable-code.md` in JavaScript
syntax: role constants above the block, one `// Data` block that ends in
`const data`, an array of records (one object per row, keyed by the
constants), and plot code below `// Plot` that reads fields with `d[QUARTER]`:

```js
// Columns: set these to your data's column names
const QUARTER = "Quarter";  // role: category
const PRODUCT_LINE = "Product line";  // role: group
const SALES = "Sales (thousand USD)";  // role: value

// Data: replace this block with your own records, one object per row
const data = [
  { [QUARTER]: "Q1", [PRODUCT_LINE]: "Electronics", [SALES]: 245 },
  { [QUARTER]: "Q2", [PRODUCT_LINE]: "Electronics", [SALES]: 312 },
  { [QUARTER]: "Q1", [PRODUCT_LINE]: "Clothing", [SALES]: 178 },
  { [QUARTER]: "Q2", [PRODUCT_LINE]: "Clothing", [SALES]: 195 },
];

// Plot: reads only data and the constants above
const quarters = [...new Set(data.map((d) => d[QUARTER]))];
const lines = [...new Set(data.map((d) => d[PRODUCT_LINE]))];
Highcharts.chart("container", {
  colors: t.palette,
  xAxis: { categories: quarters, title: { text: QUARTER } },
  yAxis: { title: { text: SALES } },
  series: lines.map((line) => ({
    type: "column",
    name: line,
    data: quarters.map((q) => data.find((d) => d[QUARTER] === q && d[PRODUCT_LINE] === line)?.[SALES] ?? null),
  })),
  // … palette, chart, credits, animation and chrome as in "Theme-adaptive chrome"
});
```

- Categories, groups and their order come from the records (`new Set` keeps
  the order of appearance), never from a typed list.
- The palette goes in whole as `colors: t.palette`; Highcharts hands out the
  first n in order.
- Axis titles and series names come from the constants.
- A missing value stays `null`, which Highcharts draws as a gap.
- Limits come from the data or stay automatic, never typed numbers.

The "Use with my data" agent will later replace the block with
`const data = window.ANYPLOT_DATA;`. Do not read that global yourself: the
harness does not set it.

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

**Pin the color scheme: `palette: { colorScheme: t.theme }`.** Since
Highcharts 13, every color you leave at its default (marker outlines,
column/pie borders, tooltip, any text you do not style) comes from the
`palette` CSS variables, and the default `colorScheme: "light dark"` follows
the *viewer's* OS dark-mode setting. Unpinned, `plot-light.html` opened on a
dark-mode machine draws dark borders and a dark tooltip on the light page.
In the dark theme those defaults are Highcharts' own dark background
(`#141414`), so a default marker outline or column border is near-black there:
set `marker.lineColor` / `borderColor` from the tokens wherever the outline
itself carries data (censor ticks, custom `line`-style marker symbols).

```js
const t = window.ANYPLOT_TOKENS;
Highcharts.chart("container", {
  palette: { colorScheme: t.theme },   // "light" | "dark"; never the OS setting
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

A complete Highcharts implementation in the zones of "Data block" above:

```js
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: Highcharts | Node
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-09
//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const DAY = "Day";  // role: category
const VISITS = "Visits";  // role: value

// Data: replace this block with your own records, one object per row
const data = [
  { [DAY]: "Mon", [VISITS]: 12 },
  { [DAY]: "Tue", [VISITS]: 19 },
  { [DAY]: "Wed", [VISITS]: 7 },
  { [DAY]: "Thu", [VISITS]: 15 },
  { [DAY]: "Fri", [VISITS]: 11 },
];

// Plot: reads only data and the constants above
Highcharts.chart("container", {
  palette: { colorScheme: t.theme },
  chart: { type: "column", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "bar-basic · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  xAxis: { categories: data.map((d) => d[DAY]),
           title: { text: DAY, style: { color: t.inkSoft, fontSize: "16px" } },
           lineColor: t.inkSoft, tickColor: t.inkSoft,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } } },
  yAxis: { title: { text: VISITS, style: { color: t.inkSoft, fontSize: "16px" } },
           gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } } },
  legend: { enabled: false },
  plotOptions: { series: { animation: false },
                 column: { borderWidth: 0 } },
  series: [{ name: VISITS, data: data.map((d) => d[VISITS]), colorByPoint: true }],
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
// Library: Highcharts | Node
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-09
```

After the review scores the plot, `impl-review.yml` replaces the header block,
from `// anyplot.ai` through the `// Quality:` line, with a four-line header that
carries the score. The rewrite keeps every `//#` directive line: the header stays
on line 1, and a directive written above it moves directly below it. Put the
`//# anyplot-orientation:` directive on its own line directly below the header
block, as the script skeleton shows.

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
- **Data-label gap is `dataLabels.distance`** (Highcharts 13, default 4 px):
  `padding` no longer pushes the label off its point or column. Set `distance`
  for the gap; keep `x` / `y` for deliberate offsets.
- **`dataSorting` is not available**: since Highcharts 13 it lives in
  `modules/data-sorting.js`, which is not loaded. Sort the data array yourself.
- **`stackLabels` formatters:** `this.isNegative` was removed in 13.1; test
  `this.total < 0` instead.
- **`useHTML` content sits in a `<div>`** (Highcharts 13, was a `<span>`), so
  inline-flow layout tricks shift; style the inner markup explicitly. Keep
  rotated labels as SVG text: rotated `useHTML` labels log invalid
  `foreignObject` transforms in 13.1.
- **Legend symbols take `series.opacity`** (Highcharts 13, column-type series):
  a legend-only proxy series hidden with `opacity: 0` shows an empty legend key.
  Hide a proxy with `color: "transparent"` plus `legendSymbolColor: <key color>`.
- **Unsorted line data needs `cropThreshold: Infinity`.** A `line` series whose
  x values are not ascending (null-separated paths, contours, graticules) is
  cropped by x range once it exceeds 300 points, which silently drops segments;
  Highcharts 13 drops different ones than 12 did.
