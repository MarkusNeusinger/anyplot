### Added

- **`derive`, a computed number column in `prepare_data`.** The assistant can
  add a ratio, a difference, a row sum, a share of a group's total, or a percent
  change from the previous row, computed server-side in pandas from a closed set
  of formulas (no free expressions), so it answers "which year has the largest
  share of foreigners?" by deriving the share instead of asking you to add the
  column. (#12179)
- **A reply-language check for the assistant.** After each final reply, an
  offline classifier compares the reply's language with the session language;
  on a sure mismatch the assistant is asked once more to write the same reply in
  the session language. (#12179)

### Changed

- **Constant text columns of a paste move to the notes.** A pasted column with
  the same text in every row, such as `Kanton` = `Schweiz` in a statistics
  export, becomes a note line (`Kanton: Schweiz`), as a one-category JSON-stat
  dimension already did, unless fewer than two columns would remain. (#12179)

### Fixed

- **A category named `NA` no longer turns into a missing value.** The exported
  loader reads only empty cells as missing when the data has a text column, so
  `NA` (Namibia, North America) from a JSON key or a JSON-stat category
  survives, and a pasted `NA` in a column of letter codes stays a code. (#12179)
