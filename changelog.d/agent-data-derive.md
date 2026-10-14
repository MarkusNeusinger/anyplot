### Added

- **`derive`, a computed number column in `prepare_data`.** The assistant can
  add a ratio, a difference, a row sum, a share of a group's total, or, in the
  order of a number or date column, a percent change from the previous row, a
  running total or an index (first row = 100), computed server-side in pandas from a closed set
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
  dimension already did, unless fewer than two columns would remain; when the
  notes are not kept, the columns come back. (#12179)

### Fixed

- **A category named `NA` no longer turns into a missing value.** The exported
  loader reads missing values per column when the data has a text column (only
  the empty cell in text, the usual tokens elsewhere), so `NA` (Namibia, North
  America) from a JSON key or a JSON-stat category survives, a pasted `NA` in a
  column of letter codes stays a code, and an R export with `NA` in a number
  column still loads. (#12179)
