### Added

- **Text files go into the agent chat's data box by drop, `.open()` or paste.**
  The browser sniffs the binary formats first (a spreadsheet or Parquet file
  is answered with "a later step, copy the cells for now", pickle and HDF5 with
  "never"), finds the encoding (UTF-8 with or without a byte order mark, Excel's
  UTF-16LE "Unicode text", UTF-16BE, windows-1252 rather than ISO-8859-1, whose
  C1 range the parser refuses) and fills the box with the file's text unchanged;
  the user presses `.parse()`, a box with text asks before it is replaced, and a
  running step refuses the file. The name travels as the dataset route's new
  `source` field, never inside the text, where it would break a JSON document:
  the agents service sanitises it, pre-filters it on its own and adds
  `source file: <name>` to the notes, which the scope judge reads in the same
  call. Plausible gets `agent_data_file{kind, encoding, outcome}`, never the
  name.
