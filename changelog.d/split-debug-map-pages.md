### Changed

- **DebugPage and MapPage split into sections.** `DebugPage.tsx` shrinks from
  1,853 to 541 lines: its KPI grid, charts, tables, and feedback blocks move
  into `app/src/sections/debug/`. `MapPage.tsx` shrinks from 1,291 to 265
  lines: its selection, search, and resize logic moves into hooks with tests,
  and the canvas, legend, hover panel, search pill, and weights panel into
  `app/src/sections/map/`. Both pages render the same markup as before.
  PalettePage stays as it is for now.
