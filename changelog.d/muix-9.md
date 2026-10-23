### Changed

- **MUI X implementations are generated against @mui/x-charts 9.16, React 19
  and @mui/material 9.5.** The pinned render stack in the root `package.json`
  moves up from @mui/x-charts 7.29.1, React 18.3.1 and @mui/material 5.18.0,
  matching the React and Material versions the frontend already runs.
  `prompts/library/muix.md` gains a "MUI X v9 API" section on the changes that
  break or silently restyle generated code: `ChartsContainer` instead of
  `ChartContainer`, `hideLegend` and the new legend position values, the HTML
  legend's extra height, `position: "none"` instead of `leftAxis={null}`, the
  per-chart CSS classes and `[data-series]`, and the line-mark defaults. The
  Sizing section adds that each axis needs an explicit `height` or `width` once
  its fonts grow, because v9 truncates tick labels that don't fit its band.
  The render harness itself needed no change. Existing MUI X implementations
  were written for v7: 164 of 323 no longer bundle under v9, and most of the
  rest render differently, so they need regeneration before they can be
  re-rendered.
