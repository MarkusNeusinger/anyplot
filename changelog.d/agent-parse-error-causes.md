### Added

- **JSON Lines in the agent chat's data box.** A paste or a dropped file with
  one JSON object per line (a log export, `to_json(lines=True)`) reads as JSON
  records, source format `json_lines`; a line that is no object is refused with
  its line number and the JSON error. A title above the objects becomes a note,
  and a dropped `.jsonl` file of one record is one row. Live test round 6 had
  refused a 600-line `events.ndjson` as unreadable. (#12201)
- **A damaged file names its broken part.** A spreadsheet, Parquet, Arrow or
  NumPy file the converter refuses as damaged says which part is broken: the
  zip container, the workbook, a sheet's cells, a Parquet footer or page, an
  Arrow stream, a NumPy header or its data. The names are a closed set carried
  from the sandbox to the page, never an exception's text (owner decision of
  2026-10-16). (#12201)

### Changed

- **A refused paste says what it fails on.** The agents service answers
  `unparseable` and `too_long` with a `cause`, which the BFF passes on one
  capped line (cut at a word, control characters removed) and the page shows
  in place of its own text: "the header has 3 fields, but line 3 has 4; line 4
  has 2", the line and column of a JSON or Python error counted from the
  paste's first line, the row and length of an over-long cell, the actual row
  count past the cap. Owner rule of 2026-10-16: people paste reasonably clean
  data, but a refusal names its cause. (#12201)
- **Ragged rows are listed, never repaired.** A table with values past its
  header's last column names every ragged line with its field count, short
  ones included; empty fields past the last column are left out with a counted
  warning, and the warning about short rows names their lines. (#12201)

### Fixed

- **The reply after a plot no longer asks to confirm confirmed data.** A
  shipped plot's tool result tells the root `data_confirmed: true`, and its
  prompt says that only the current session block decides whether the data is
  confirmed, so an earlier turn's "please confirm" is not repeated (live test
  round 6, R6-1). (#12201)
