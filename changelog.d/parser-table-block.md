### Changed

- **Pasted data with notes, metadata or a total around the table parses.** The agent's
  parser finds the table among the pasted lines by its data rows: a title, an export's
  metadata (such as the two lines above an Open-Meteo download's header) or a sentence
  that explains the columns above it, a source line or a note below it, and up to three
  summary rows at the end (`Total`, `Summe`, `Mittelwert`…) are left out, each with a
  warning in the preview. Before, the first line was always the header, so a raw
  Open-Meteo download lost its data columns.
