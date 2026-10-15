### Added

- **Date column from year and month in the agent chat.** A new `prepare_data`
  operation, `make_date`, builds a date column from whole-number columns that
  hold the parts of a date: a year with a month and an optional day, a quarter,
  or an ISO week. Out-of-range values and rows that are no calendar date are
  refused, never moved. `set_type` to a date also reads `DD/MM/YYYY`,
  `YYYYMMDD`, `YYYYMM`, `YYYY-MM`, `MM/YYYY`, `MM.YYYY` and `YYYY`. The root prompt now
  uses these operations and no longer asks the user to add a column that an
  operation can build. (#12193)

### Fixed

- **Default bindings skip non-measures and codes.** A number role that holds
  measures no longer takes a constant column, a year, or a month, quarter or
  week number when another column fits. An optional measure role stays empty
  instead. A series or category role prefers a name column such as `Austria`
  over a code column such as `AT` that splits the rows the same way. (#12193)
