### Added

- **Derived columns in the data step.** `prepare_data` takes four new
  operations: `compute` adds a number column from an expression over number
  columns (a product, a power, a log, a unit conversion), checked by the
  whitelist `generate_data` already runs and computed exactly for whole
  numbers; `diff` adds the change from the row one or n places before;
  `rolling` adds a mean or a sum over the last n rows; and `blank` empties
  missing-value codes such as `-0.99` in place while the rows stay. The
  first rows of each group, a missing input, a division by zero and a value
  outside a function's domain leave a cell empty, and the change line counts
  each. It came from the persona tests of 2026-11-06, where five of ten
  personas got no plot because a column could not be derived.
- **The last value per month, over several columns.** `aggregate` takes
  `columns`, two to ten value columns with one reduction, and the reductions
  `first` and `last`, by time when a key is a date column, so the last meter
  reading of each month is one operation.
- **Several values into one category.** A condition takes `values`, an "any
  of" list for `eq` and `contains`, so `classify` puts `Miete` and `Strom`
  into one label, and its change line names how many rows fell to the
  fallback and their three largest groups.
- **The chat names what it cannot do.** A change no operation can make, such
  as filling in values, is the `unsupported` operation: it changes nothing,
  answers a fixed sentence in the session language that never sends the user
  to a spreadsheet, and counts the gap by its family in the `chat_turn`
  telemetry (`capability_gap`).

### Changed

- **The prep eval covers the new operations.** Ten cases on invented data,
  one per persona need, and the Fahrenheit case now expects a `compute`. A
  `compute` matches by the values it computes, whatever short names and form
  the expression has. The first run matched 91 of 96 cases for $0.27.
