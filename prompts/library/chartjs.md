# Chart.js

Chart.js is the most popular open-source JavaScript charting library — simple,
flexible, HTML5-canvas based. This is one of anyplot's first JavaScript-language
entries; the file extension is **`.js`** and the runtime is the **browser render
harness** (`node automation/js-render/render.mjs`), **not** Python, Rscript, or
julia.

**API level:** Chart.js 4. The root `package-lock.json` pins this major; write
against its API.

JavaScript charts render in a browser DOM — there is no headless CLI that writes
a PNG. You author an **idiomatic Chart.js snippet** that draws into the mount
node `#container`; the harness wraps it in an HTML page, loads the pinned
`chart.js` bundle, renders it under headless Chromium (Playwright), and
screenshots the mount node at the exact canvas size. It emits **both**
`plot-{theme}.png` (gallery + og:image) and `plot-{theme}.html` (interactive
detail view). You never call `savefig`/`save` — you never even touch the
filesystem.

## IMPORTANT: No Workarounds

**If Chart.js cannot implement a plot type natively, DO NOT shell out to D3,
ECharts, a plugin, or any other library.** Chart.js ships eight core chart
types (bar, line, scatter, bubble, pie, doughnut, radar, polarArea) plus mixed
charts. If a spec genuinely cannot be expressed with core Chart.js, return
`NOT_FEASIBLE` rather than reaching for a sibling library or an unpinned plugin.

Out of scope for this entry:
- D3-style bespoke/low-level SVG layouts → that is the `d3` entry.
- Chart types that only exist in `chartjs-chart-*` community plugins (sankey,
  treemap, matrix, etc.) — those plugins are **not** installed in the runtime.
  Do not `import` them; return `NOT_FEASIBLE` if the spec's core value needs one.

**Computation:** Chart.js has no statistics helpers, so short written-out
binning, box statistics, densities or fits are fine.

## The mount-node contract (how your snippet connects to the harness)

The harness gives you a pre-sized `<div id="container">` and these globals (the
browser has no `process.env`, so this is the JS analogue of `ANYPLOT_THEME`):

```js
window.ANYPLOT_THEME      // "light" | "dark"
window.ANYPLOT_TOKENS     // { pageBg, elevatedBg, ink, inkSoft, grid, palette[8], amber, seq[2], div[3] }
window.ANYPLOT_SIZE       // { width, height } — the CSS mount size
window.Chart              // the Chart.js global (already loaded)
```

Your snippet must:
1. Create a `<canvas>` and append it to `#container`.
2. Build the chart with `new Chart(canvas, config)`.
3. Set `responsive: true`, `maintainAspectRatio: false`, **`animation: false`**.

Do **not** set the canvas `width`/`height` attributes and do **not** size the
container — the harness owns exact pixels. `animation: false` is mandatory: the
harness screenshots after a render-settle, and an animating chart screenshots
mid-tween.

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (the `impl-review.yml`
gate rejects anything off by more than 16 px and re-triggers repair):

| Orientation | Pixels      | How                                        |
|-------------|-------------|--------------------------------------------|
| Landscape   | 3200 × 1800 | default                                    |
| Square      | 2400 × 2400 | add directive `//# anyplot-orientation: square` |

The harness produces these exactly via Playwright `deviceScaleFactor: 2` over a
fixed mount (1600×900 or 1200×1200 CSS). You do **not** compute pixels — you only
pick orientation. For a square spec (pie/doughnut/radar/polarArea), put this on
its own line directly below the header block (see "Header Style"):

```js
//# anyplot-orientation: square
```

## Reproducibility

Generate data in-memory and deterministically. There is no seeded RNG in the
browser; if you need pseudo-randomness, use a tiny fixed-seed LCG or hard-code
the data array. **Never `fetch()` or load from a CDN/network** — the runtime is
offline and the HTML must be self-contained.

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
  { [QUARTER]: "Q3", [PRODUCT_LINE]: "Electronics", [SALES]: 287 },
  { [QUARTER]: "Q4", [PRODUCT_LINE]: "Electronics", [SALES]: 425 },
  { [QUARTER]: "Q1", [PRODUCT_LINE]: "Clothing", [SALES]: 178 },
  { [QUARTER]: "Q2", [PRODUCT_LINE]: "Clothing", [SALES]: 195 },
  { [QUARTER]: "Q3", [PRODUCT_LINE]: "Clothing", [SALES]: 285 },
  { [QUARTER]: "Q4", [PRODUCT_LINE]: "Clothing", [SALES]: 310 },
];

// Plot: reads only data and the constants above
const quarters = [...new Set(data.map((d) => d[QUARTER]))];
const lines = [...new Set(data.map((d) => d[PRODUCT_LINE]))];
const datasets = lines.map((line, i) => ({
  label: line,
  data: quarters.map((q) => data.find((d) => d[QUARTER] === q && d[PRODUCT_LINE] === line)?.[SALES] ?? null),
  backgroundColor: t.palette[i],
}));
// … new Chart(canvas, { type: "bar", data: { labels: quarters, datasets }, options: { scales: {
//   x: { title: { display: true, text: QUARTER } }, y: { title: { display: true, text: SALES } } } } })
```

- Categories, groups and their order come from the records (`new Set` keeps the
  order of appearance), never from a typed list.
- Each group takes its palette position (`t.palette[i]`).
- Axis titles and series labels come from the constants.
- A missing value stays `null`, which Chart.js draws as a gap.
- Limits come from the data or stay automatic, never typed numbers.

The "Use with my data" agent will later replace the block with
`const data = window.ANYPLOT_DATA;`. Do not read that global yourself: the
harness does not set it.

## Colors — Imprint palette (from `window.ANYPLOT_TOKENS`)

The first categorical series is **always** `#009E73` (`tokens.palette[0]`).
Multi-series follows the palette order. Data colors are **identical** between
light and dark — only chrome (text, grid, background) flips.

```js
const t = window.ANYPLOT_TOKENS;
// single series
backgroundColor: t.palette[0]            // #009E73 brand green
// multi series: one palette position per series, never recycled (no `i % t.palette.length`)
const datasets = lines.map((line, i) => ({ label: line, backgroundColor: t.palette[i] /* , data: … */ }));
// one dataset colored per category (pie, doughnut): the same rule per label
backgroundColor: quarters.map((_, i) => t.palette[i])
```

Never use `viridis`/`rainbow`/`jet` or arbitrary hex. For continuous color use
`t.seq` (`["#009E73", "#4467A3"]`) or `t.div` (`["#AE3030", midpoint, "#4467A3"]`,
midpoint is theme-adaptive and already baked into `t.div`).

## Theme-adaptive chrome (Chart.js mapping)

Read the tokens and map them onto Chart.js options. The page background is the
mount background (`t.pageBg`) — do not paint a white plot area.

```js
const t = window.ANYPLOT_TOKENS;
options: {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    title:  { display: true, text: "spec-id · javascript · chartjs · anyplot.ai", color: t.ink, font: { size: 22 } },
    legend: { labels: { color: t.ink, font: { size: 16 } } },
  },
  scales: {
    x: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid }, title: { display: true, text: DAY, color: t.ink } },
    y: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid }, title: { display: true, text: VISITS, color: t.ink } },
  },
}
```

Pie/doughnut/radar/polarArea have no cartesian scales — drop the `scales` block
and rely on `plugins` + per-arc `backgroundColor`.

## Script Skeleton

A complete Chart.js implementation reads the theme tokens, generates data,
appends a canvas to `#container`, and builds the chart. The same single `.js`
file handles both themes (the harness sets `window.ANYPLOT_THEME` per render).
It follows the zones of "Data block" above.

```js
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: chartjs | JavaScript
// Quality: pending | Created: 2026-06-02
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
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
  type: "bar",
  data: {
    labels: data.map((d) => d[DAY]),
    datasets: [{ label: VISITS, data: data.map((d) => d[VISITS]), backgroundColor: t.palette[0], borderWidth: 0 }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title:  { display: true, text: "bar-basic · javascript · chartjs · anyplot.ai", color: t.ink, font: { size: 22 } },
      legend: { labels: { color: t.ink, font: { size: 16 } } },
    },
    scales: {
      x: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid },
           title: { display: true, text: DAY, color: t.ink } },
      y: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid }, beginAtZero: true,
           title: { display: true, text: VISITS, color: t.ink } },
    },
  },
});
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/javascript/chartjs.js` —
  rendered twice by the harness with different `ANYPLOT_THEME`.
- Generated artifacts (written by the harness, not the snippet):
  `plot-light.png` + `plot-dark.png` and `plot-light.html` + `plot-dark.html`
  (Chart.js is in `INTERACTIVE_LIBRARIES`).

## Header Style

JavaScript has no docstring; anyplot uses a leading `//` comment block, mirroring
the Python/R/Julia conventions:

```js
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: chartjs | JavaScript
// Quality: pending | Created: 2026-06-02
```

After the review scores the plot, `impl-review.yml` replaces the header block,
from `// anyplot.ai` through the `// Quality:` line, with a four-line header that
carries the score. The rewrite keeps every `//#` directive line: the header stays
on line 1, and a directive written above it moves directly below it. Put the
`//# anyplot-orientation:` directive on its own line directly below the header
block, not merged into it, as the script skeleton shows.

## Chart.js-Specific Gotchas

- **`animation: false` is mandatory.** Without it the screenshot catches a
  half-grown bar / partially-swept arc.
- Do **not** set `canvas.width` / `canvas.height` or a fixed container size — the
  harness sizes the mount and owns the final pixels.
- Chart.js auto-handles `devicePixelRatio`; do not pass `devicePixelRatio` in the
  config (the page already runs at 2×).
- Append exactly one canvas to `#container`; do not leave stray DOM nodes.
- No `import`/`require` and no `<script src=…>` — `Chart` is already a global.
- Tooltips/hover are interactive-only and never appear in the static PNG; that is
  expected. Do not try to force a tooltip open for the screenshot.
