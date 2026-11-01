### Fixed

- **The agent's reply names the texts the plot draws, in all 15 libraries.**
  In the user test of 2026-11-01, replies for Chart.js, bokeh and pygal plots
  said the plot's title and labels could not be read back, and a Makie reply
  offered a title the plot already had. Only matplotlib, seaborn and plotnine
  reported their drawn texts. Now pygal, altair and lets-plot report them
  through the render harness; Chart.js, D3, ECharts, Highcharts, MUI X, plotly
  and bokeh through the browser harness; and ggplot2 and Makie through a text
  probe their renderer rows load, each by the library's own roles (title, axis
  labels, ticks, legend, annotations). The probes are best-effort: a failure
  drops the labels and is logged, never fails the render, and adds at most
  0.55 s (Makie). The requested-text check stays with the reviewer for these
  libraries, and G12 stays matplotlib's. (#12503)
- **A render without drawn texts no longer hands the root a `null`.** The
  root gets `shows` without `texts`, its prompt no longer mentions unread
  texts, and it never claims a text is absent from what `texts` leaves out.
  The eval report counts shipped runs without drawn texts per library
  (`untexted`), quotes in replies that no drawn text holds
  (`unbacked_quotes`), and failed probes. (#12503)
