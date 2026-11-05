### Fixed

- **The progress grid stands still from `.create_plot()` to the result.** After
  the data card folded, the run's `starting…` or `queued · 1 of 2` line above
  the grid went away at the first step, and the grid jumped up one line beside
  the loader (27 px at desktop and phone width). With each step, the cells
  after the active one also slid right by about 11 px, because a step still to
  come had no marker. Now where the run stands shows in the first try's outcome
  cell. Every marker has a slot of the same width, and the label and first step
  columns are sized for `second try` and `repairing` from the start. While the
  run lasts the page also has no scroll anchoring, which had scrolled the page
  by a repair round's new row (25 px at desktop width, 65 px at phone width).
  The agent BFF mock gains `MOCK_START_MS`, which holds a run before its first
  step, and `MOCK_REPAIR=1`, which gives a first plot a repair round. (#12569)
- **One queue position, which moves nothing.** A plot run names its place in
  the queue only in the progress grid's first row. The badge above the composer
  used to come and go there too, moving the grid and the composer 33.5 px down
  and back. A turn without the grid keeps the badge, now beside its in-progress
  line and out of the flow. (#12569)
- **The bindings say why they wait in their heading.** While the assistant
  works or the data is parsed, the heading reads `# bindings — wait while the
  assistant works` (or `… the data is parsed`) and then swaps back. The
  separate line under it read as the heading twice and moved the dropdowns
  25.5 px as it came and went. (#12569)
