<!--
The JavaScript runtime's passages of the adapter prompt (Chart.js, D3, ECharts and Highcharts, since 2026-10-30,
JS-4a of step 3): `policy.adapter_prompt("javascript")` puts each slot below into the `{{slot}}` of the same name in
`adapter.md`, which holds every rule the languages share, so a shared rule changes in one place. These passages
tell the adapter JavaScript's conventions: the placeholder `const data = loadUserData();` and how the server types
the table it puts into the page (`data/typed_json.py`, `code/profiles/javascript/loader.py`), the column constants
read as `d[COL]` (the "Data block" of `prompts/library/<library>.md`), the protected statements
(`code/profiles/javascript/regions.py`), what the validator refuses (`code/profiles/javascript/validate.py`),
the `null` conversions JavaScript makes silently, and the time axes kept in UTC so the exported page shows the
same dates in any browser's time zone (measured in the JS-2 renderer image on 2026-10-30: D3's `scaleUtc`,
ECharts' `useUTC`, Highcharts' `datetime` axis, Chart.js without a date adapter; Highcharts writes `8k` and a
space for thousands unless its labels go through `fmt`). `tests/unit/agents/runtime/test_policy.py` runs the
idioms through both validator profiles, and `tests/unit/agents/code/test_profile_javascript_image.py` renders them.
A slot runs from its `slot:` comment to the next one; the blank lines around it are not part of it. This comment
never reaches a model.
-->

<!-- slot: request_formatter -->
a tick format such as `(v) => fmt(v / 1e6, 1) + " Mio."` (`fmt` as under **Numbers** below) that writes the decimal comma and the unit

<!-- slot: requested_check -->
A JavaScript render has no probe, so the server cannot read its drawn texts back: the reviewer looks for each requested text in the image instead, and reports one it cannot find, which then comes back to you as a finding.

<!-- slot: measured_hints -->
A JavaScript render has no probe, so no hint is ever a target measured on a render: every hint quotes the code.

<!-- slot: density_check -->
A JavaScript render has no probe, so no gate counts the labels for you: the host gates judge only its output, the PNG and its canvas, so count the marks from `data` yourself.

<!-- slot: data_statement -->
The code is JavaScript, a classic script in a browser page that draws with the library's page global (`Chart` for Chart.js, `d3`, `echarts`, `Highcharts`). The data comes from exactly one statement at the top level:

```js
const data = loadUserData();
```

It returns an array with one object per row, keyed by exactly the loader columns under their exact names, spaces, units and punctuation included, with the names in `data.columns` (the shape `d3.csvParse` returns). The values are typed: `integer` and `number` as numbers (an integer past ±2^53 as the nearest double, which the server announces), `boolean` as `true` and `false`, `text` as strings (also a cell that looks like a number, such as `001`), dates as `YYYY-MM-DD` strings and timestamps as UTC ISO strings with milliseconds (`2024-01-31T07:00:00.000Z`: an offset converted, digits below the millisecond cut). A missing cell is `null`. The server replaces the statement with the read of the table it puts into the page when it runs the code, so never write that read (`window.ANYPLOT_DATA`), never parse a CSV yourself and never read a file. Where the rules below say `df`, they mean `data`.

<!-- slot: data_columns -->
- When the working form has no `const data = loadUserData();` line yet (the first attempt), replace the block that creates the example data (literal arrays and objects of values, random draws, the formulas behind the invented data, and the variables built from them) with that single line, and rewrite the plot code to read from `data`. Most catalogue JavaScript files keep their example values in variables of their own (`quarters`, `revenueByProduct`), so rewrite every use of such a variable to the column it stands for.
- Name each column once, in a column constant set to its exact bound name, as the library rules' "Data block" below shows: `const REVENUE = "Revenue (EUR)";  // role: y`. Keep the constants the code has, set their values to the bound columns, and add one for a column the code does not name yet. Write the name as a double-quoted string, with `\"` and `\\` for a quote and a backslash, never as a template literal, where `${` runs code. Read every column through its constant, as `d[REVENUE]`, never as a property (`d.Revenue`), which breaks on a column name with a space or a unit.

<!-- slot: data_order -->
- Keep the data's first-appearance order for categories (`[...new Set(data.map((d) => d[GROUP]))]`), never a sorted order, unless they are ordered (ordinal) categories, such as sizes, ratings, age bands or month and weekday names, which keep their natural order. A sort the spec asks for (bars by value) still applies: sort a copy (`[...data].sort(...)`), never `data` itself.
- A missing cell is `null`, and JavaScript converts it without a word: `+null`, `Number(null)` and `null * 2` are `0`, `new Date(null)` is 1 January 1970, `String(null)` and a template are `"null"`, `d[DAY].slice(...)` throws on it, and `Math.max(...values)` reads it as `0`. Drop the rows a mark needs before any conversion or statistic (`data.filter((d) => d[Y] != null)`), or hand the `null` to the library where it draws a gap (a Chart.js, ECharts or Highcharts series, D3's `d3.line().defined((d) => d[Y] != null)`); never draw a missing value as zero or as a category called `null`.
- Never create data: no random draws to make values (`d3.randomNormal` and the other distribution draws; `Math.random`, `d3.randomUniform`, `d3.randomInt` and `d3.shuffle` only for jitter or subsampling are allowed), no literal arrays of more than 20 numbers, no file reads, no downloads.

<!-- slot: protected_lines -->
- the orientation directive on the first line, `//# anyplot-orientation: landscape` (or `square`), which picks the canvas;
- every theme token line, a top-level statement that reads the page's tokens or tests an earlier token, such as `const t = window.ANYPLOT_TOKENS;`, `const { width, height } = window.ANYPLOT_SIZE;`, `const isDark = window.ANYPLOT_THEME === "dark";` or `const MUTED = isDark ? "#A8A79F" : "#6B6A63";`. A line that also reads another name, such as one that picks a value from the data by theme, is ordinary plot code that you may change;
- the `const data = loadUserData();` line once it exists. Keep it out of `find` and `replace`, also to append to it: to transform `data` or add statements after it, use the line below it as `find` and write the new statements in front of that line in `replace`.

Each of these statements stands alone on its lines and binds its names once: never assign a token again or change one in place (`t.palette.push(...)`, `t.ink = ...`, `Object.assign(t, ...)`), never put other code on their lines, and never assign to `window.ANYPLOT_TOKENS`, `window.ANYPLOT_THEME`, `window.ANYPLOT_SIZE` or `window.ANYPLOT_DATA` (reading the first three is fine; `window.ANYPLOT_DATA` is the server's read alone).

<!-- slot: canvas -->
The canvas is fixed by the server: the page's `#container` has the size the orientation directive picks (1600 by 900 CSS pixels at twice the pixel density, 1200 by 1200 for `square`), and the server screenshots that element. Never change or add the directive, never set the size of `#container`, `body` or the page, and size the chart from the container: `window.ANYPLOT_SIZE` for D3's `svg` (its `width` and `height`), `responsive: true` with `maintainAspectRatio: false` for Chart.js, `echarts.init(document.getElementById("container"))` without a size, and Highcharts' chart in `"container"` without `chart.width` or `chart.height`. Keep animation off (`animation: false` in Chart.js and ECharts, on Highcharts' `chart` and its series), because the screenshot is taken once the page settles, and keep the title in the call that shows it.

<!-- slot: palette_literal -->
in JavaScript the page's token array `t.palette`, never a list in the code (it already holds all eight Imprint positions in order, so there is never a position to append as described below and never an `IMPRINT` or `IMPRINT_PALETTE` of your own to write, and `INK_MUTED` goes after the token lines, since there is no palette line); you never assign, copy or change it, and the page sets it

<!-- slot: palette_builders -->
`.concat()`, a spread, `.slice()`, `.push()`, `.map()` or a loop

<!-- slot: palette_lookup -->
`t.palette[i]` with each group's position in `groups = [...new Set(data.map((d) => d[GROUP]))]`, or the whole array where the library hands its colors out in order (ECharts' `color: t.palette`, Highcharts' `colors: t.palette`, D3's `d3.scaleOrdinal().domain(groups).range(t.palette)`)

<!-- slot: ink_muted -->
const INK_MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

<!-- slot: computed_text -->
a string built with `fmt` (under **Numbers** below: `"r = " + fmt(r, 2)`, with `r` computed from `data` through the column constants of the code)

<!-- slot: number_formatting -->
JavaScript's `toFixed` and `String` write `.` for decimals and no thousands mark, and each library's default axis format is its own (Chart.js, ECharts and D3's `d3.format` write English marks, Highcharts writes `8k` and a space for thousands): format through one function,

<!-- slot: number_output -->
`en`: `"."` and `","`): `const fmt = (v, digits = 2) => { const r = Number(v.toFixed(digits)); const [whole, frac] = Math.abs(r).toFixed(digits).split("."); return (r < 0 ? "-" : "") + whole.replace(/\B(?=(\d{3})+(?!\d))/g, THOUSANDS) + (frac ? DECIMAL + frac : ""); };` as every value axis's tick format (Chart.js `ticks: { callback: (v) => fmt(v, 1) }`, D3 `.tickFormat((v) => fmt(v, 1))`, ECharts `axisLabel: { formatter: (v) => fmt(v, 1) }`, Highcharts `labels: { formatter() { return fmt(this.value, 1); } }`) and for value labels, tooltips and annotations, never a bare `v.toFixed(2)`, `String(v)` or `d3.format(",.2f")`, which always write English marks. Years, dates, identifiers and the cells of the user's data stay as they are. A plot language the table does not list keeps the catalogue's formats. No gate checks the decimal marks of a JavaScript render, which has no probe, so the code alone keeps them right.

<!-- slot: dates -->
`new Date(d[DAY])` reads a date cell (`2024-01-31`) as its UTC midnight and a timestamp cell as its UTC instant; drop the rows without one first (`const dated = data.filter((d) => d[DAY] != null);`), because `new Date(null)` is 1 January 1970 and a string method throws on `null`. Keep every time axis in UTC, so the plot shows the same dates in the server's render and in the exported page in any browser's time zone: D3's `d3.scaleUtc()` with `d3.utcFormat("%d.%m.%Y")` (never `d3.scaleTime` or `d3.timeFormat`, which use the browser's zone); ECharts' `useUTC: true` with a `type: "time"` axis and `[new Date(d[DAY]).getTime(), d[Y]]` points; Highcharts' `type: "datetime"` axis with the same points (it shows UTC) and `labels: { format: "{value:%d.%m.%Y}" }`. The page has no date adapter for Chart.js, whose `type: "time"` axis fails: put dates on its category axis as text, rewritten with string methods (`labels: data.map((d) => d[DAY].slice(0, 10).split("-").reverse().join("."))`: the slice keeps the date of a timestamp cell, which is the whole ISO string, and `d[DAY].slice(11, 16)` is its UTC clock time), or, for uneven spacing, on a linear axis as `new Date(d[DAY]).getTime()` with a tick callback that writes the date back (`new Date(v).toISOString().slice(0, 10)`). Write dates in numeric formats: month and weekday names come out in English unless you give `toLocaleDateString` the plot language's locale and `timeZone: "UTC"`.

<!-- slot: safe_code -->
Draw with the library's page global (`Chart`, `d3`, `echarts` or `Highcharts`, the one the code already uses) and the language's built-ins that compute (`Math`, `Number`, `String`, `Array`, `Set`, `Map`, `Date`, `Intl`, `JSON`, and `Object.keys`, `values`, `entries`, `fromEntries` and `assign`); never `import`, `export` or `require`. Reach the page only through `document.getElementById("container")`, `document.createElement` and `createElementNS` for a `canvas`, `div` or SVG element, and the token globals of the protected lines. No network, storage or other windows: no `fetch`, `XMLHttpRequest`, `WebSocket`, `navigator`, `localStorage`, `sessionStorage`, `document.cookie`, `window.open`, `location`, `postMessage`, `Worker`, `Image`, `Blob` or `URL`, no D3 loaders (`d3.csv`, `d3.json`, `d3.image`) and no Highcharts `ajax` or `getJSON`. No code from strings: no `eval`, `Function`, `import()`, `setTimeout` or `setInterval` with a string, no `script`, `iframe`, `object`, `embed`, `link`, `form` or `base` element, no `innerHTML` with markup that loads or runs, no `.write()`. A cell or a column name can hold markup, so text from the data never goes into `innerHTML` or an HTML string (a tooltip formatter that returns HTML): set `textContent`, or the library's plain text option. Use `window` and `document` only with a named member (`window.ANYPLOT_SIZE`, `document.getElementById`), never as a value, by a computed key (`window[name]`) or as `globalThis`, `self`, `top` or `parent`; no `constructor`, `__proto__` or `with`, and `this` only inside a library callback that sets it (Highcharts' `formatter() { return fmt(this.value, 0); }`, D3's `each`). Never set `src`, `href` or an `on...` attribute. No URL and no string literal longer than 200 characters.

<!-- slot: placeholder -->
const data = loadUserData();

<!-- slot: highlight_compute -->
`const peak = data.filter((d) => d[Y] != null).reduce((best, d) => (best === null || d[Y] > best[Y] ? d : best), null)` (`null` when no row has a value: then draw no highlight), `fmt(peak[Y], 0)`
