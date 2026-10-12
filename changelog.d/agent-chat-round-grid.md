### Changed

- **The plot run's progress is a grid of rounds that says how each round ended.** One
  row per round (`first try`, `repair 1`), the same four steps lined up in the same
  columns, and the outcome on the right: `✓ ok`, `✗ review: 3 findings`,
  `✗ 2 measured`, `✗ code check failed`, or `~ 1 finding open` for a shipped result
  that still needs attention. The step a round stopped at is marked. The pipeline
  reports each round's outcome as `PlotResult.rounds` and on the `repairing` status,
  and the result card keeps the grid under `# rounds` (#12150).
