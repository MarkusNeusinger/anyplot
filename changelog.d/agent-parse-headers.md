### Fixed

- **The agent chat reads headers in comment lines and under an export's metadata.** A
  data file that opens with `#`, `%` or `//` comment lines keeps them as notes, and when
  its table has no header line, the last one or two comment lines name the columns,
  placed by the columns' character ranges, so a monthly series whose header wraps over
  two `#` lines reads `decimal date` and `monthly average` instead of `#`, `date`,
  `alized`. A statistics export's header of years under key-value metadata is the header
  again, a key-value line no longer joins a header, a `:` cell is missing in a number
  column, and a column of one-letter flags beside a year stays as `<year> flag` with a
  warning that counts the flags. A title above a header of years no longer turns the
  table into one column of text. (#12602)
- **A statistics export's legend below the table stays out of the rows.** A
  spreadsheet export pads every line to the table's width, so the legend under the
  table (`:,not available`, `p,provisional`) read as rows without values and turned a
  year column into text. Such rows now extend the table only up to a blank line; the
  legend after it is kept as notes below the table, so the assistant can say what `:`
  and the flags mean. (#12602)
- **A pasted Markdown table keeps its column names.** The row of dashes under a Markdown
  table's header (`|---|:---:|`), as chat assistants write it, became part of the names
  (`Month -------`, `:------`) or a row of a column of names. It is now left out as
  layout when it stands directly under the header; a row of dashes further down the
  table stays a row. (#12602)
