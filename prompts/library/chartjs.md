# Chart.js

Chart.js is the most popular open-source JavaScript charting library — simple,
flexible, HTML5-canvas based. This is one of anyplot's first JavaScript-language
entries; the file extension is **`.js`** and the runtime is the **browser render
harness** (`node automation/js-render/render.mjs`), **not** Python, Rscript, or
julia.

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
its own line near the top of the file (it can sit just below the header block):

```js
//# anyplot-orientation: square
```

## Reproducibility

Generate data in-memory and deterministically. There is no seeded RNG in the
browser; if you need pseudo-randomness, use a tiny fixed-seed LCG or hard-code
the data array. **Never `fetch()` or load from a CDN/network** — the runtime is
offline and the HTML must be self-contained.

## Colors — Imprint palette (from `window.ANYPLOT_TOKENS`)

The first categorical series is **always** `#009E73` (`tokens.palette[0]`).
Multi-series follows the palette order. Data colors are **identical** between
light and dark — only chrome (text, grid, background) flips.

```js
const t = window.ANYPLOT_TOKENS;
// single series
backgroundColor: t.palette[0]            // #009E73 brand green
// multi series
backgroundColor: categories.map((_, i) => t.palette[i % t.palette.length])
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
    x: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid }, title: { display: true, text: "X", color: t.ink } },
    y: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid }, title: { display: true, text: "Y", color: t.ink } },
  },
}
```

Pie/doughnut/radar/polarArea have no cartesian scales — drop the `scales` block
and rely on `plugins` + per-arc `backgroundColor`.

## Script Skeleton

A complete Chart.js implementation reads the theme tokens, generates data,
appends a canvas to `#container`, and builds the chart. The same single `.js`
file handles both themes (the harness sets `window.ANYPLOT_THEME` per render).

```js
//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const labels = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const values = [12, 19, 7, 15, 11];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [{ label: "Visits", data: values, backgroundColor: t.palette[0], borderWidth: 0 }],
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
      x: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid } },
      y: { ticks: { color: t.inkSoft, font: { size: 14 } }, grid: { color: t.grid }, beginAtZero: true },
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
// Library: chartjs 4.4 | JavaScript 22
// Quality: pending | Created: 2026-06-02
```

The pipeline's `impl-review.yml` header-rewrite replaces the leading `//` block
once a quality score is assigned. It deliberately skips `//#`-prefixed lines, so
your `//# anyplot-orientation:` directive survives — keep the directive on its
own line, not merged into the header.

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
