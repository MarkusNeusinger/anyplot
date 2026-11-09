### Fixed

- **The plot button takes pasted data whenever Enter would.** One pure rule
  (`plotClick` in `plotChain.ts`) now decides both whether the button is
  active and what its click does, so the two can no longer disagree. With the
  admin's `all` pressed, a pasted table left `.plot_all()` inert and only Enter
  read it. Now the one click reads the table and opens the fan-out once it
  reads clean. A table typed over stored data is read first too, never plotted
  as the old data's fan-out or sent as a plot request. Short, 5 KB and
  spreadsheet pastes on a fresh page are covered by unit and page tests.
  (#13019)
