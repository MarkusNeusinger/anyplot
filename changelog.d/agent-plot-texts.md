### Fixed

- **The agent's reply names the texts the plot draws in ten more libraries.**
  In the user test of 2026-11-01, replies for Chart.js, bokeh and pygal plots
  said the plot's title and labels could not be read back. Only matplotlib,
  seaborn and plotnine reported their drawn texts. Now pygal, altair and
  lets-plot report them through the render harness, and Chart.js, D3, ECharts,
  Highcharts, MUI X, plotly and bokeh through the browser harness, each by the
  library's own roles (title, axis labels, ticks, legend, annotations). The
  requested-text check stays with the reviewer for these libraries, and G12
  stays matplotlib's. ggplot2 and Makie follow separately. (#12503)
- **A render without drawn texts no longer hands the root a `null`.** The
  root gets `shows` without `texts` and its prompt no longer mentions unread
  texts, so it describes the change instead of saying it could not read the
  plot. The eval report counts shipped runs without drawn texts per library
  (`untexted`). (#12503)
