### Added

- **The JavaScript code profile for "Use with my data", not served yet.**
  `agents/anyplot/code/profiles/javascript/` reads Chart.js, D3, ECharts and
  Highcharts code with the pinned tree-sitter grammar for JavaScript and MUI X
  code with the one for TSX (the agents image now keeps both): the protected
  token lines that read the harness's `window.ANYPLOT_*` globals and the
  orientation directive, a normaliser that strips the header, writes one
  directive on the first line and blanks the catalogue title, a SECURITY and
  ADAPTATION validator that resolves scopes and admits a closed world of
  global names (the network, storage, frames, workers, `eval`, `Function`,
  `import()`, `require`, `.constructor`, string timers, elements that load,
  aliasing and computed access on `window`, `this` where it may be the window,
  keys built to spell `constructor`, protocol-relative URLs and writes that
  navigate or load a URL the code did not draw are refused, with the named
  bypasses as tests), MUI X imports checked against a copy of the renderer
  image's import allowlist that a test and CI compare with the image's, the
  readiness scan (93 clean, 1,456 coupled, 68 blocked; MUI X files written
  for 7.29 are coupled with a note naming the imports MUI X 9 lacks), the
  one-line loader `const data = window.ANYPLOT_DATA;`, and an error grammar
  that reads the harness's final error line without its message. The edit
  applier gains a JavaScript dialect (`//` and `/* */` comments, a `#` in a
  string stays text) and the export a `//` header that names the exported
  `plot.html`, with the other languages' output unchanged; the runtime, the
  prompts and the fixtures follow in JS-4.
