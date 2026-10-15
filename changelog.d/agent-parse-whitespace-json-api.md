### Added

- **The agent chat reads tables aligned with spaces.** A weather or statistics
  office's `.txt` (MeteoSwiss' homogenised monthly series in the live test of
  2026-10-15) came in as one text column. Where no comma, semicolon, tab or
  pipe finds a table, the parser now splits at runs of two or more spaces, so a
  header such as `Max Temp` stays one name, and at single spaces only for a
  table of numbers; prose, a headerless list (`Hund 7`), a key-value block and a
  table with two-word names still go to the transcriber. A blank cell of a
  fixed-width row stays in its column by position, and a row that does not line
  up is refused rather than guessed. The metadata block above the table becomes
  notes, and a declared mark such as `Missing values: -999` reads as missing in
  number and date columns. (#12191)
- **The agent chat reads JSON as data APIs answer it.** The World Bank's
  `[{page metadata}, [records]]` was refused. Records wrapped with metadata (an
  array beside a metadata object, or `{"data" | "results" | "records": [...]}`
  with sibling fields) and schema-plus-rows payloads (BigQuery, CKAN, Socrata,
  pandas `orient="split"`) now read, the metadata going to the notes; nested
  objects become dotted columns (`country.value`) down to three levels, and
  list fields such as a measured curve's `x` and `y` expand to one row per
  point, with a `record_id` when nothing else tells the records apart. (#12191)

### Fixed

- **The assistant names only controls the chat page has.** Asked to read only
  the table of a paste, it told the user to choose "a separator that recognises
  spaces", a setting that does not exist. Its prompt now lists every control of
  the page and says to suggest re-pasting only the table when its tools cannot
  fix the data; a unit test checks each named control against the page's code.
  (#12191)
- **The dataset pre-filter reads constant columns too.** A constant text column
  moved to the notes returned to the stored table when the notes were dropped,
  without the instruction pre-filter having read it. (#12191)
