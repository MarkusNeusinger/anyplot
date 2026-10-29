### Changed

- **Per-route page metadata uses React 19 native hoisting.** Pages render
  bare `<title>`, `<meta>` and `<link rel="canonical">` elements instead of
  wrapping them in `react-helmet-async`, which is archived upstream; the
  dependency and its `HelmetProvider` are gone. The `/plots` title is now
  declarative too and keeps the route name next to the active filters
  (`lib:matplotlib | plots | anyplot.ai`); `useUrlSync` no longer writes
  `document.title`. (#12424)
