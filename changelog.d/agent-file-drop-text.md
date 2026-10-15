### Added

- **Text files go into the agent chat's data box by drop, `.open()` or paste.**
  The browser sniffs the binary formats first (a spreadsheet, Parquet, Arrow or
  NumPy file is answered with "a later step, copy the cells or export as CSV
  for now", pickle and HDF5 with "never"), finds the encoding (UTF-8 with or
  without a byte order mark, Excel's UTF-16LE "Unicode text", UTF-16BE,
  windows-1252 rather than ISO-8859-1, whose C1 range the parser refuses) and
  fills the box with the file's text, line breaks as `\n`; the user presses
  `.parse()`, a box with text asks before it is replaced, and a running step
  refuses the file. The name travels as the dataset route's new `source` field,
  never inside the text and never as a note: the agents service sanitises it,
  screens it on its own call and keeps it as the dataset's `file_name`, which
  the assistant reads fenced as data, a name and never a request, so a file
  named like a wish for the plot is not acted on. Plausible gets
  `agent_data_file{kind, encoding, outcome}`, never the name. (#12192)
