### Added

- **Render and unit tests for the palette, debug, and map sections.** Vitest
  suites under `app/src/sections/palette/`, `app/src/sections/debug/`, and
  `app/src/sections/map/` cover the components split out of `PalettePage`,
  `DebugPage`, and `MapPage`: the hue–chroma wheel, comparison palettes,
  snippet tabs, the WCAG swatch stroke per theme, the spec matrix headers and
  filters, feedback triage, and the map legend, hover panel, search pill,
  force weights, and canvas shell. The state that lives in the pages is tested
  on the real pages: `PalettePage.test.tsx` covers the swatch copy reset and
  the CVD sort order, and `DebugPage.test.tsx` the spec sort orders, the
  incomplete and low-score filters, and the feedback status PATCH with its
  revert. Every behaviour the review named was checked by breaking it on
  purpose and watching a test fail. (#12470)
