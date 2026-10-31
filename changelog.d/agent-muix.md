### Added

- **MUI X in "Use with my data", for the admin's live tests.** The JavaScript
  runtime serves MUI X (`muix`) next to Chart.js, D3, ECharts and Highcharts:
  `plot.tsx`, a React module the renderer's harness bundles through its closed
  import plugin and mounts as a component, with the user's table as typed JSON.
  The admin deploy names it, so 13 of the 15 catalogue libraries are served, and
  its 80 % eval matrix gates the public release. A catalogue file written for
  MUI X 7 is served `coupled` with its `deprecated-api` note, never blocked for
  its version (owner decision): the adapter rewrites `ChartContainer` to MUI X
  9.16's `ChartsContainer`. The interactive `plot.html` and the in-chat preview
  work for MUI X's React bundle as for the other four.
- **MUI X idioms in the JavaScript adapter prompt.** `adapter_javascript.md`
  teaches what was measured with MUI X 9.16 in the renderer image: the module's
  imports and its one default export, MUI X 9's names for MUI X 7's, axis bands
  sized for the user's labels (MUI X cuts tick labels that do not fit), overlays
  drawn through the chart's own scales instead of pixel positions from `margin`,
  a `"utc"` time axis with a formatter (a `"time"` axis follows the browser's
  zone in the exported page), `fmt` on every value axis (MUI X writes
  `1,250,000`), and a series formatter that guards `null`, which MUI X hands it
  when a reader hovers a gap; unguarded, the hover removes the whole chart. A
  test runs the idioms through both validator profiles, and an image test
  renders them from a table with missing cells in both themes.
- **MUI X eval fixtures.** The ten matrix specs for MUI X (60 cases, 780
  generated in all) and the smoke case `pie-basic-muix-renamed`; five of the
  ten files are `clean` (written for MUI X 9.16), five `coupled`, one of them
  with the `deprecated-api` note. Across the catalogue 311 of 323 MUI X files
  are eligible.

### Fixed

- **The eval matrix's preflight with a MUI X 7 file first.** The preflight
  rendered the catalogue file of each library's first case unchanged, and a MUI X
  file written for MUI X 7 fails the bundle step until the adapter rewrites it,
  so a selection starting with one (`scatter-basic-*`) stopped before any case.
  It now renders the library's first selected case whose file bundles as it
  stands, or, when none does (`scatter-basic-muix-*` alone), the library's smoke
  case, so the case that tests the rewrite can run on its own.
- **The page probe hovers the plot, not a legend mark.** `page_probe.mjs`
  hovered the first canvas or svg in the plot's frame, which in a MUI X page is
  a legend entry's 10-pixel mark; it hovers the largest now. The renderer
  image's CI builds and probes a MUI X page next to the Chart.js one.
