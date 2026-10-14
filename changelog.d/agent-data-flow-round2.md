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
  them, before the 50-column check, unless fewer than two columns would remain. (#12182)
- **Grouped thousands read as numbers.** `7.184.003`, `1,234,567`, `1,234.5`,
  Swiss `1'234'567` and space-grouped `1 234,5` (also with no-break and thin
  spaces) are numbers instead of text; a `1,234` column is read as thousands in a
  file with dot decimals, and keeps its decimal comma without a needless warning
  in a file that writes `6,07`. Dotted dates stay dates. (#12182)
- **Default bindings take a measure as the value and a category or the year as
  the category.** A text column of numbers ranks after a year column for a
  category role, a real category of 2 to 60 values ranks first, and a value role
  ranks year columns after every measure; a time axis prefers the year. (#12182)
- **A step-2 note that narrows the bindings keeps the confirmation and its
  title.** Bindings set by the assistant that only leave out confirmed roles
  ("only co2_per_capita") keep the user's confirmation (`AGENT_NARROWED_BINDINGS`,
  default `keep`), so the plot runs in the same turn; a first plot's request that
  stops on `data_unconfirmed` is kept for the next `.create_plot()`. (#12182)
