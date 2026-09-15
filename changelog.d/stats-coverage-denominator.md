### Fixed

- **Coverage matrix on the stats page counted against 9 libraries instead of
  15.** Every cell tooltip read `15/9` for a fully covered spec, and the
  "possible implementations" total was short by the same factor, because the
  page carried a hardcoded library count from back when nine were supported.
  `/insights/dashboard` now serves `total_libraries` (the canonical
  `SUPPORTED_LIBRARIES` size that already backs `coverage_percent`) and the page
  renders against it, so the denominator follows the library set instead of
  drifting from it.

### Changed

- **Coverage cells read as three states, not a gradient.** Cells grew from 10 px
  to 14 px and full coverage now renders as solid brand green while anything
  short of it carries an amber outline (dashed when a spec has no
  implementation at all), with a labelled legend replacing the less/more ramp.
  The interesting signal is which specs are *not* complete, and those are the
  minority — the old opacity ramp made them the hardest cells to pick out. The
  summary line also names how many specs are below full coverage.
