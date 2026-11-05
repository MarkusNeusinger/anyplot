### Fixed

- **Two flaky tests no longer turn main red.** The adaptability checker's
  design-example test read live catalogue files, so the nightly regeneration
  of line-basic's seaborn file broke it; the two examples now come from
  fixtures under `tests/unit/core/fixtures/adaptability/design/`. The
  validator's per-file CPU budget now measures only the validator's own thread
  with the garbage collector paused: the process-wide CPU time also counted
  the test worker's other threads and heap collections, which pushed 3 ms files
  past the 1 s budget (`network-weighted/matplotlib`,
  `heatmap-periodic-table/plotnine`).
