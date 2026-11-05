### Fixed

- **The progress grid stands still from `.create_plot()` to the result.** After
  the data card folded, the run's `starting…` or `queued · 1 of 2` line above
  the grid went away at the first step, and the grid jumped up one line beside
  the loader (27 px at desktop and phone width). With each step, the cells
  after the active one also slid right by about 11 px, because a step still to
  come had no marker. Now where the run stands shows in the first try's outcome
  cell. Every marker has a slot of the same width, and the label and first step
  columns are sized for `second try` and `repairing` from the start, so the
  grid also holds still when a repair round's row joins it. The agent BFF mock
  gains `MOCK_START_MS`, which holds a run before its first step so that
  `starting…` stays visible.
