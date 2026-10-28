### Changed

- **Per-route page metadata uses React 19 native hoisting.** Pages render
  bare `<title>`, `<meta>` and `<link rel="canonical">` elements instead of
  wrapping them in `react-helmet-async`, which is archived upstream; the
  dependency and its `HelmetProvider` are gone.
