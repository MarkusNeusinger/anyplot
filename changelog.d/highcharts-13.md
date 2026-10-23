### Changed

- **Highcharts renders with 13.1.1 instead of 12.6.0.** The JavaScript render
  harness pins the latest 13.x release, which also carries the fixes for the
  2026-09 core security advisories (prototype pollution through `series.keys`,
  `javascript:` URLs in `credits.href` and exported markup). The generator
  prompt now pins `palette: { colorScheme: t.theme }`, because Highcharts 13
  takes every default color from CSS variables that otherwise follow the
  viewer's OS dark-mode setting in the interactive HTML. It also covers the
  13.x changes a before/after render of all 323 Highcharts implementations
  surfaced: the `dataLabels.distance` gap, legend symbols that take
  `series.opacity`, near-black default outlines in the dark theme, and the
  cropping of unsorted line data. Existing implementations stay as they are,
  and regeneration refreshes them.
