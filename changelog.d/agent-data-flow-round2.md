### Added

- **The assistant answers questions about the data without changing it.** A new
  root tool, `query_data`, applies the same closed set of operations as
  `prepare_data` to a copy of the data and returns at most 25 rows in at most 8
  columns; nothing is stored, so the data version, the bindings and the
  confirmation stay as they are. In the live test the root had filtered the
  user's table to one year to answer "which country was highest in 2023?" and
  then asked the user to undo it; the prompt now sends questions to
  `query_data` and keeps `prepare_data` for changes the user asked for. (#12182)

### Fixed

- **Empty columns leave a pasted table.** A column with a header but no value
  in any row (an ECB export carried 14) is dropped with one warning that names
  them, before the 50-column check, for JSON records and column lists too. (#12182)
- **Grouped thousands read as numbers.** `7.184.003`, `1,234,567`, `1,234.5`,
  Swiss `1'234'567` and space-grouped `1 234,5` (also with no-break and thin
  spaces) are numbers instead of text; a `1,234` or `1.234` column follows a
  grouped column of the same file, and a decimal comma keeps no needless warning
  in a file that writes `6,07`. Dotted dates, IP addresses, single space groups
  (`123 456`) and columns named as ids, codes, versions or phone numbers stay as
  they are. (#12182)
- **Default bindings take a measure as the value and a category or the year as
  the category.** A text column of numbers ranks after a year column for a
  category role, a real category of 2 to 60 values ranks first, and a value role
  ranks year columns after every measure; a time axis prefers the year. A price
  in the year range counts as a year only with a year name or a full yearly
  run. (#12182)
- **A step-2 note that drops a line keeps the confirmation and its title.**
  Bindings set by the assistant that only leave out confirmed number series
  ("only co2_per_capita") keep the user's confirmation (`AGENT_NARROWED_BINDINGS`,
  default `keep`), so the plot runs in the same turn; any other binding change
  asks for `.confirm()` again. A first plot's request that stops before the plot
  is kept until a plot ships, and dropped by any later change to the bindings or
  the data. (#12182)
