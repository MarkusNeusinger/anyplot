### Added

- **JSON Lines in the agent chat's data box.** A paste or a dropped file with
  one JSON object per line (a log export, `to_json(lines=True)`) reads as JSON
  records, source format `json_lines`; a line that is no object is refused with
  its line number and the JSON error. Live test round 6 had refused a 600-line
  `events.ndjson` as unreadable. (#12201)

### Changed

- **A refused paste says what it fails on.** The agents service answers
  `unparseable` and `too_long` with a `cause`, which the BFF passes on one
  capped line and the page shows after its own text: "the header has 3 fields,
  but line 3 has 4; line 4 has 2", the line and column of a JSON or Python
  error, the row and length of an over-long cell, the actual row count past
  the cap. Owner rule of 2026-10-16: people paste reasonably clean data, but a
  refusal names its cause. A damaged spreadsheet, Parquet, Arrow or NumPy file
  names the format its first bytes claimed. (#12201)
- **Ragged rows are listed, never repaired.** A table with values past its
  header's last column names every ragged line with its field count, short
  ones included; empty fields past the last column are left out with a counted
  warning, and the warning about short rows names their lines. (#12201)

### Fixed

- **The reply after a plot no longer asks to confirm confirmed data.** The
  root's prompt says that only the current session block decides whether the
  data is confirmed and that a shipped plot was made from confirmed data, so an
  earlier turn's "please confirm" is not repeated (live test round 6, R6-1). (#12201)
