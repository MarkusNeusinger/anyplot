# MUI X Charts

MUI X Charts (`@mui/x-charts`) is the charting component set for the **MUI
(Material UI) React** ecosystem — SVG-rendered bar, line, pie, scatter and more,
styled to feel native in a Material dashboard. In anyplot it is a **React**
entry: the file extension is **`.tsx`**, `language_id` is **`javascript`**
(React is a runtime constraint, not a language), and it renders through the
**browser render harness** (`node automation/js-render/render.mjs`) via that
harness's **React (esbuild) branch** — *not* Python, Rscript, or julia.

> ## 🚫 Community surface ONLY — no MUI X Pro / Premium (hard rule)
>
> anyplot vendors **only** the **MIT-licensed community package `@mui/x-charts`**.
> The commercial **`@mui/x-charts-pro`** and **Premium** tiers (advanced zoom &
> pan, export, large-dataset perf, heatmap-pro, etc.) are **out of scope and
> strictly forbidden** — they are not installed, and importing them will fail the
> build outright. **Never** import from any of these:
>
> - ❌ `@mui/x-charts-pro` (and every `@mui/x-charts-pro/*` subpath)
> - ❌ `@mui/x-charts-premium` / any `*-premium` package
> - ❌ any component/prop documented as "Pro" or "Premium" only (e.g. `<ChartsZoomAndPan />`, the Pro-only `zoom`/`export` toolbar features)
>
> ✅ Import **only** from `@mui/x-charts` (and `@mui/x-charts/<Chart>` subpaths),
> plus `@mui/material` / `@mui/system` for styling. **Within that community
> surface you are encouraged to use the full richness MUI X offers** — add axes,
> legends, custom marks, reference lines, stacking, multiple series, tooltips,
> labels, gradients, whatever genuinely serves the spec. The rule is *not* "keep
> it minimal"; it is "**everything you use must be community `@mui/x-charts`**."

## The harness contract (how your `.tsx` connects)

Unlike Chart.js / D3 / ECharts (which imperatively draw into `#container`), a MUI
X snippet is a **React component**. You author one file that **default-exports a
component**; the harness does everything else:

1. it **esbuild-bundles** your file together with `react`, `react-dom`,
   `@mui/x-charts`, `@mui/material`, `@emotion/*`;
2. it wraps your component in a **MUI `ThemeProvider`** whose palette follows
   `ANYPLOT_THEME` (so axis ticks, legend text and chrome are already
   theme-adaptive — you don't wire that yourself);
3. it mounts it with `createRoot(...).render(...)` into the pre-sized
   `#container`, waits for render-complete, and Playwright-screenshots at the
   exact canvas size, also emitting the self-contained interactive HTML.

So your file must:

- **`export default`** a React function component (the harness renders it with
  **no props**).
- **Not** call `ReactDOM.render` / `createRoot`, build any HTML, wrap itself in
  its own `ThemeProvider`, or drive a screenshot — the harness owns all of that.
- Import its chart components from `@mui/x-charts` (e.g.
  `import { BarChart } from "@mui/x-charts/BarChart";`).

```tsx
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;            // see "Globals" below

export default function Chart() {
  return (
    <BarChart
      width={window.ANYPLOT_SIZE.width}
      height={window.ANYPLOT_SIZE.height}
      colors={t.palette}
      skipAnimation
      xAxis={[{ scaleType: "band", data: ["Mon", "Tue", "Wed", "Thu", "Fri"] }]}
      series={[{ data: [12, 19, 7, 15, 11], label: "Visits" }]}
    />
  );
}
```

> The snippet is only ever **bundled by esbuild**, never type-checked by `tsc`, so
> reading untyped browser globals (`window.ANYPLOT_TOKENS`) is fine — no `as any`
> needed. esbuild strips the TS/JSX and emits plain JS.

## Globals the harness injects

The browser has no `process.env`, so these globals are the JS analogue of
`ANYPLOT_THEME` (already read for you by the harness's `ThemeProvider`, but
available if you want the raw values):

```js
window.ANYPLOT_THEME    // "light" | "dark"
window.ANYPLOT_TOKENS   // { pageBg, elevatedBg, ink, inkSoft, grid, palette[8], amber, seq[2], div[3] }
window.ANYPLOT_SIZE     // { width, height } — the CSS mount size (size the chart to this)
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (the `impl-review.yml`
gate rejects anything off by more than 16 px and re-triggers repair):

| Orientation | Pixels      | How                                             |
|-------------|-------------|-------------------------------------------------|
| Landscape   | 3200 × 1800 | default                                         |
| Square      | 2400 × 2400 | add directive `//# anyplot-orientation: square` |

Exact pixels come from Playwright `deviceScaleFactor: 2` over the pre-sized mount
(1600×900 / 1200×1200 CSS). **Size the chart to `window.ANYPLOT_SIZE`**
(`width={window.ANYPLOT_SIZE.width} height={window.ANYPLOT_SIZE.height}`) — never
hard-code other dimensions. For a square spec (pie / radial / heatmap-style),
put this on its own line at the very top of the file:

```tsx
//# anyplot-orientation: square
```

## Sizing — CSS px in the mount's coordinate space (NOT native 3200 px)

The mount is **1600×900** (landscape) / **1200×1200** (square) CSS px; the 2×
device scale lands the PNG on 3200×1800 / 2400×2400. Size fonts/marks in that CSS
space — small numbers like the other JS libs. MUI X defaults are already sized
for CSS px; only nudge `tickLabelStyle` / `slotProps` font sizes if labels look
small at the final resolution (axis/legend ≈ 14–16 px, title ≈ 22 px).

## Animation — must be off (static screenshot)

A static PNG must capture the **final** frame, never a half-grown bar. The
harness emulates `prefers-reduced-motion: reduce` (MUI X honours it), **and** you
must pass **`skipAnimation`** on the chart so the first paint is the final paint.
Always set both belts — set `skipAnimation` on every chart component.

## Theme — let the ThemeProvider handle chrome; set data colours yourself

The harness's `ThemeProvider` maps `ANYPLOT_TOKENS` onto MUI's palette
(`mode`, `text.primary = ink`, `text.secondary = inkSoft`, `background`), so axis
ticks, axis lines, and legend text are **already theme-adaptive** — light ink on
the cream page, light ink on the dark page. You only supply the **data colours**:

```tsx
const t = window.ANYPLOT_TOKENS;
// Categorical: first series is ALWAYS brand green (t.palette[0]).
<BarChart colors={t.palette} … />
// Continuous (e.g. heatmap / colour scale): build from the Imprint stops —
//   sequential: [t.seq[0], t.seq[1]]
//   diverging : [t.div[0], t.div[1], t.div[2]]
```

Data colours are **identical** between light and dark — only the chrome flips
(handled by the theme). Never use MUI X's default category palette or a named
gradient (viridis / rainbow). The `#container` background is already `t.pageBg`;
MUI X charts are transparent, so the page shows through — do **not** paint a white
background.

## Reproducibility

Generate data in-memory and deterministically. There is no seeded RNG in the
browser; use a tiny fixed-seed LCG or hard-code the data. **Never `fetch()` or
load from a CDN/network** — the runtime is offline and the HTML must be
self-contained.

## When MUI X can't express the spec

MUI X community covers bar, line, area, pie, scatter, sparkline, gauge, radar,
funnel, and composed/multi-axis combinations. If the spec's core value is a chart
type the **community** surface genuinely can't express (and it isn't a Pro-only
feature you're tempted to reach for), return **`NOT_FEASIBLE`** with a one-line
reason — **do not** shell out to Recharts/D3/Chart.js or reach into
`@mui/x-charts-pro`.

## Output Files

- Implementation: `plots/{spec-id}/implementations/javascript/muix.tsx` —
  rendered twice by the harness with different `ANYPLOT_THEME`.
- Generated artifacts (written by the harness, not the snippet):
  `plot-light.png` + `plot-dark.png` and `plot-light.html` + `plot-dark.html`
  (MUI X is in `INTERACTIVE_LIBRARIES`).

## Header Style

```tsx
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-09
```

The `impl-review.yml` header-rewrite replaces the leading `//` block and skips
`//#` directive lines, so a `//# anyplot-orientation:` line survives — keep it on
its own line at the very top.

## Script Skeleton

```tsx
//# anyplot-orientation: landscape
// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-09
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const categories = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const values = [12, 19, 7, 15, 11];

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <BarChart
      width={window.ANYPLOT_SIZE.width}
      height={window.ANYPLOT_SIZE.height}
      colors={t.palette}
      skipAnimation
      xAxis={[{ scaleType: "band", data: categories }]}
      series={[{ data: values, label: "Visits" }]}
    />
  );
}
```

## Forbidden patterns

- **No `@mui/x-charts-pro` / `@mui/x-charts-premium`** or any Pro/Premium-only
  feature — community `@mui/x-charts` only (see the hard rule at the top).
- **No other charting libraries** — no Recharts, Nivo, Visx, Chart.js, D3,
  ECharts. `muix` demonstrates MUI X only; fall back to `NOT_FEASIBLE` instead.
- **No manual mount / HTML** — no `ReactDOM.render`, no `createRoot`, no
  `document.body` plumbing, no inline `<html>`/screenshot code. Default-export a
  component; the harness mounts and screenshots it.
- **No CDN / `fetch` / network** — the runtime is offline; the emitted HTML must
  be self-contained.
- **No white background** and **no MUI X default category palette / named
  gradients** — use the Imprint palette from `window.ANYPLOT_TOKENS`.
- **No left-on animation** — always `skipAnimation`.

## MUI X-Specific Gotchas

- **`export default` is mandatory** — the harness imports the component as the
  module's default export and renders it with no props. A named-only export
  renders nothing and fails the draw check.
- **`skipAnimation` is mandatory** — without it the screenshot can catch a
  mid-tween frame (bars not yet at full height).
- Size with `width`/`height` from `window.ANYPLOT_SIZE`; don't hard-code 3200 px
  (that's the post-`deviceScaleFactor` size, not the CSS mount size).
- Tooltip / hover highlighting is interactive-only and won't appear in the static
  PNG — that's expected; don't force it open for the screenshot.
- MUI X measures real SVG text (getBBox) for axis/legend layout, which is exactly
  why the browser harness is used — verify labels aren't clipped at the final
  resolution and add axis `margin` / `slotProps.legend` spacing if they are.
