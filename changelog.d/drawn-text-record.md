### Changed

- **The chat's record of a plot's drawn texts names what it leaves out, adds
  measured axis ranges for matplotlib and seaborn plots, and captures Chart.js
  canvas annotations.** In "Use with my data", each role of `PlotShows.texts`
  used to be a plain head slice (up to 8 tick labels or annotations) with no
  marker, so a 12-month axis reached the assistant as 8 labels that looked like
  the whole axis, and axis ranges were read from tick labels rather than axis
  limits. Each drawn role now ships as a record (`ShownRole`) with `count` (the
  number of distinct texts recorded in that role) and either `texts` (every text
  in drawing order, up to 20 for x and y tick labels and 16 for annotations) or
  `first` and `last` (the two ends of a longer run), `PlotShows.texts_complete`
  marks when the probe stopped before every drawn text (omitted when `true` or
  when `texts` is absent or empty, which `fence_pipeline_notes` drops),
  `requested_not_found` still checks the full probe output, and the reply figure
  check ignores `count` as a number source. For matplotlib and seaborn plots
  (plotnine maps its scales before matplotlib and reports none),
  `PlotShows.axes` reports the measured `min`, `max`, and `scale` (`linear`,
  `log`, or `date` as ISO 8601) of the first two non-empty rectilinear
  non-colorbar axes with `axison` on (`x`, `y`, and `z` for 3D axes, skipping
  hidden axes, axes with no visible tick label, `matplotlib.category`
  converters/formatters/locators, hand-set tick labels, non-finite limits, and
  `other`-scaled axes), credited as `drawn_text` in the figure check, and the
  assistant states axis ranges only from `axes`. In sandbox mode, the
  JavaScript text probe also wraps `fillText` and `strokeText` for Chart.js,
  keeping each chart's last complete draw and subtracting model-reported texts
  by count so plugin-drawn value labels and doughnut center numbers reach the
  assistant as `annotations`; fully transparent text and text of size 0 are
  not recorded, and a render run records through the page the browser loads
  while the `plot-<theme>.html` it writes carries no recorder.
