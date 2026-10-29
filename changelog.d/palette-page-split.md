### Changed

- **PalettePage split into sections.** `PalettePage.tsx` shrinks from 1,783 to
  144 lines: its colour helpers, sub-components (`ChromaWheel`, `CodeBlock`,
  `DeltaEMatrix`), and eight numbered sections move into
  `app/src/sections/palette/`. The page keeps only state, effects, memos, and
  layout, and renders the same markup as before. (#12463)
