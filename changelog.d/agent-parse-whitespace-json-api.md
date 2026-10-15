### Added

- **The agent chat reads tables aligned with spaces.** A weather or statistics
  office's `.txt` (MeteoSwiss' homogenised monthly series in the live test of
  2026-10-15) came in as one text column. The parser now splits at runs of two
  or more spaces, so a header such as `Max Temp` stays one name, or at single
  spaces when every line has the header's field count; prose and a headerless
  list (`Hund 7`) still go to the transcriber. A blank cell of a fixed-width row
  stays in its column by position. The metadata block above the table becomes
  notes, and a declared mark such as `Missing values: -999` reads as missing.
- **The agent chat reads JSON as data APIs answer it.** The World Bank's
  `[{page metadata}, [records]]` was refused. Records wrapped with metadata (an
  array beside a metadata object, or `{"data" | "results" | "records": [...]}`
  with sibling fields) now read, the metadata going to the notes; nested objects
  become dotted columns (`country.value`) down to three levels, and a field that
  holds a list is left out with a warning.

### Fixed

- **The assistant names only controls the chat page has.** Asked to read only
  the table of a paste, it told the user to choose "a separator that recognises
  spaces", a setting that does not exist. Its prompt now lists every control of
  the page and says to suggest re-pasting only the table when its tools cannot
  fix the data; a unit test checks each named control against the page's code.
