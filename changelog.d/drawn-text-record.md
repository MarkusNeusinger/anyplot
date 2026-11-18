### Changed

- **The chat's record of a plot's drawn texts names what it leaves out, adds
  measured axis ranges for matplotlib plots, and captures Chart.js canvas
  annotations.** In "Use with my data", each role of `PlotShows.texts` used to
  be a plain head slice (up to 8 tick labels or annotations) with no marker, so
  a 12-month axis reached the assistant as 8 labels that looked like the whole
  axis, and axis ranges were read from tick labels rather than axis limits.
  Each drawn role now ships as a record (`ShownRole`) with `count` (the number
  of distinct texts in that role) and either `texts` (every text in drawing
  order, up to 20 for x and y tick labels and 16 for annotations) or `first`
  and `last` (the two ends of a longer run), while `requested_not_found` still
  checks the full probe output and the reply figure check ignores `count` as a
  number source. For plots rendered through the matplotlib harness (matplotlib,
  seaborn, and plotnine), `PlotShows.axes` reports the measured `min`, `max`,
  and `scale` (`linear`, `log`, `date` as ISO 8601, or `other`) of the first
  two non-colorbar visible axes (`x`, `y`, and `z` for 3D axes, skipping
  categorical axes), and the assistant states axis ranges only from `axes`. In
  sandbox mode, the JavaScript text probe also wraps `fillText` and
  `strokeText` for Chart.js, keeping each chart's last complete draw and
  subtracting model-reported texts by count so plugin-drawn value labels and
  doughnut center numbers reach the assistant as `annotations`.
