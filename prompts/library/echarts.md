# Apache ECharts

Apache ECharts is a powerful, feature-complete charting and data-visualization
library for the browser (Canvas/SVG, Apache-2.0). This is one of anyplot's first
JavaScript-language entries; the file extension is **`.js`** and the runtime is
the **browser render harness** (`node automation/js-render/render.mjs`), **not**
Python, Rscript, or julia.

ECharts charts render in a browser DOM — there is no headless CLI that writes a
PNG. You author an **idiomatic ECharts snippet** that initializes a chart on the
mount node `#container`; the harness wraps it in an HTML page, loads the pinned
`echarts` bundle, renders it under headless Chromium (Playwright), and
screenshots the mount node at the exact canvas size. It emits **both**
`plot-{theme}.png` and `plot-{theme}.html`. You never write to the filesystem.

## IMPORTANT: No Workarounds

**If ECharts cannot implement a plot type natively, DO NOT shell out to
Chart.js, D3, or any other library.** ECharts has an enormous built-in catalog
(line, bar, scatter, pie, radar, heatmap, boxplot, candlestick, sankey, graph,
treemap, sunburst, parallel, themeRiver, gauge, funnel, …). If the spec's core
value is genuine interactivity (hover/zoom/brush) with no static form, return
`NOT_FEASIBLE`. Do not simulate interaction.

Do **not** `import` extra ECharts extension packages or GL (`echarts-gl`) — only
the pinned `echarts` global is available, and `echarts-gl` is not installed.

## The mount-node contract (how your snippet connects to the harness)

The harness gives you a pre-sized `<div id="container">` and these globals (the
browser has no `process.env`, so this is the JS analogue of `ANYPLOT_THEME`):

```js
window.ANYPLOT_THEME      // "light" | "dark"
window.ANYPLOT_TOKENS     // { pageBg, elevatedBg, ink, inkSoft, grid, palette[8], amber, seq[2], div[3] }
window.ANYPLOT_SIZE       // { width, height } — the CSS mount size
window.echarts            // the echarts global (already loaded)
```

Your snippet must:
1. `const chart = echarts.init(document.getElementById("container"))`.
2. `chart.setOption(option)` with `animation: false`.

Call `echarts.init` with **no explicit width/height** so it fills the mount, and
**do not pass `devicePixelRatio`** — the page already runs at 2× and ECharts
reads `window.devicePixelRatio` automatically. Passing it again double-scales and
fails the canvas gate.

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (the `impl-review.yml`
gate rejects anything off by more than 16 px and re-triggers repair):

| Orientation | Pixels      | How                                        |
|-------------|-------------|--------------------------------------------|
| Landscape   | 3200 × 1800 | default                                    |
| Square      | 2400 × 2400 | add directive `//# anyplot-orientation: square` |

The harness produces these exactly via Playwright `deviceScaleFactor: 2` over a
fixed mount; ECharts auto-sizes to the mount. You only pick orientation. For a
square spec (pie/radar/heatmap/sunburst), put this on its own line near the top:

```js
//# anyplot-orientation: square
```

## Reproducibility

Generate data in-memory and deterministically. There is no seeded RNG in the
browser; use a tiny fixed-seed LCG or hard-code the data. **Never `fetch()` or
load from a CDN/network** — the runtime is offline and the HTML must be
self-contained.

## Colors — Imprint palette (from `window.ANYPLOT_TOKENS`)

The first categorical series is **always** `#009E73` (`tokens.palette[0]`). Set
ECharts' top-level `color` array to the Imprint palette. Data colors are
**identical** between light and dark — only chrome flips.

```js
const t = window.ANYPLOT_TOKENS;
option.color = t.palette;                 // categorical cycle, first = brand green
// continuous (heatmap visualMap): build from the Imprint stops
option.visualMap = { inRange: { color: t.seq } };     // sequential
// diverging: { inRange: { color: t.div } }            // midpoint theme-adaptive
```

Never use ECharts' default palette or named gradients like `viridis`/`rainbow`.

## Theme-adaptive chrome (ECharts mapping)

Map tokens onto the chart chrome. The `#container` background is already
`t.pageBg` — leave `backgroundColor` transparent (the page shows through) or set
it to `t.pageBg`; never white.

```js
const t = window.ANYPLOT_TOKENS;
const option = {
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: { text: "spec-id · javascript · echarts · anyplot.ai", left: "center",
           textStyle: { color: t.ink, fontSize: 22 } },
  legend: { textStyle: { color: t.ink, fontSize: 16 } },
  textStyle: { color: t.inkSoft },
  xAxis: { axisLabel: { color: t.inkSoft, fontSize: 14 }, axisLine: { lineStyle: { color: t.inkSoft } },
           splitLine: { lineStyle: { color: t.grid } } },
  yAxis: { axisLabel: { color: t.inkSoft, fontSize: 14 }, axisLine: { lineStyle: { color: t.inkSoft } },
           splitLine: { lineStyle: { color: t.grid } } },
  series: [/* … */],
};
```

Pie/radar/sunburst have no `xAxis`/`yAxis` — drop those and style via `label` /
`itemStyle` instead.

## Script Skeleton

```js
//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const labels = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const values = [12, 19, 7, 15, 11];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: { text: "bar-basic · javascript · echarts · anyplot.ai", left: "center",
           textStyle: { color: t.ink, fontSize: 22 } },
  grid: { left: 80, right: 60, top: 90, bottom: 70 },
  xAxis: { type: "category", data: labels,
           axisLabel: { color: t.inkSoft, fontSize: 14 },
           axisLine: { lineStyle: { color: t.inkSoft } },
           splitLine: { show: false } },
  yAxis: { type: "value",
           axisLabel: { color: t.inkSoft, fontSize: 14 },
           axisLine: { lineStyle: { color: t.inkSoft } },
           splitLine: { lineStyle: { color: t.grid } } },
  series: [{ type: "bar", data: values, itemStyle: { color: t.palette[0] } }],
});
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/javascript/echarts.js` —
  rendered twice by the harness with different `ANYPLOT_THEME`.
- Generated artifacts (written by the harness, not the snippet):
  `plot-light.png` + `plot-dark.png` and `plot-light.html` + `plot-dark.html`
  (ECharts is in `INTERACTIVE_LIBRARIES`).

## Header Style

```js
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-02
```

The `impl-review.yml` header-rewrite replaces the leading `//` block and skips
`//#` directive lines, so the `//# anyplot-orientation:` line survives — keep it
on its own line.

## ECharts-Specific Gotchas

- **`animation: false` is mandatory** — otherwise the screenshot catches a
  mid-animation frame.
- Call `echarts.init(el)` with **no** explicit size and **no** `devicePixelRatio`
  — the mount is pre-sized and the page already renders at 2×.
- No `import`/`require`, no `<script src=…>` — `echarts` is already a global.
- Initialize exactly one chart on `#container`.
- Toolbox/dataZoom/tooltip are interactive-only and won't appear in the static
  PNG; that's expected — don't try to force them open for the screenshot.
