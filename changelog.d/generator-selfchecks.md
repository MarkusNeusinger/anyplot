### Added

- **The generator checks its file against the library prompt's mandates
  before the first render.** `contract_check.py` gains one rule per setting a
  library prompt states as mandatory, as a hard rule or as forbidden: the
  bokeh page paint and toolbar, equal pygal tick sizes and both pygal guide
  colours, altair's `autosize` fit, no plotly `autosize=True`, the lets-plot
  canvas wrap, no `bbox_inches="tight"`, and the entrance animation off in
  Chart.js, ECharts, Highcharts and MUI X. Each rule quotes the prompt's own
  words. A new `selfcheck` command prints them for the session (Step 2b of
  the generate prompt, every language), which fixes what it reports and
  writes a `Contract self-check:` line into the commit body. The review keeps
  re-running the check record-only. A regeneration had carried a line that a
  gate checks into nearly every file, but a line that is only read into
  about half: 9 of 16 replaced bokeh files painted the page, 7 of 16 pygal
  files set both tick sizes alike.
- **The generator recomputes what its plot claims.** Step 4 of the generate
  prompt now lists every claim the plot states that its data or structure
  can confirm (printed numbers and words, two parts showing one quantity,
  the legend, an axis title's sign, a named projection or interval, a
  structural rule such as one route through a maze or a check digit), checks
  each with a computation outside the file, and fixes what fails in its one
  fix round. The result goes into a `Claims self-check:` line. The review
  reads the picture and can't recompute it, so sealed mazes, a "Mercator"
  title over another projection and change indicators that contradict their
  sparkline had passed it.

### Fixed

- **lets-plot figures with a fixed aspect fill the canvas instead of
  leaving blank bands.** The canvas wrap painted the strips but left them
  empty. The library prompt now puts the legend below a fixed-aspect panel,
  picks the canvas by the figure with its title and legend, and widens a
  map's shorter span from the data. On scratch renders this took the blank
  share of two square maps from about a quarter of the height to a twentieth.
