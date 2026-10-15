### Added

- **Date column from year and month in the agent chat.** A new `prepare_data`
  operation, `make_date`, builds a date column from whole-number columns that
  hold the parts of a date: a year with a month and an optional day, a quarter,
  or an ISO week. Out-of-range values and rows that are no calendar date are
  refused, never moved. `set_type` to a date also reads `DD/MM/YYYY`,
  `YYYYMMDD`, `YYYYMM`, `YYYY-MM`, `MM/YYYY`, `MM.YYYY` and `YYYY`. The root prompt now
  uses these operations and no longer asks the user to add a column that an
  operation can build. (#12193)
- **Month names, date order and computed roles in the agent chat.** `make_date`
  reads month names and abbreviations in eleven languages. A date column whose
  day and month could be read either way can be switched in both directions,
  also in a later version. A new date column fills an open required date
  role. A role the plot computes, such as the rolling average of
  `line-timeseries-rolling`, takes no column. (#12193)

### Fixed

- **Default bindings skip non-measures and codes.** A number role that holds
  measures no longer takes a constant column, a year, or a month, quarter or
  week number when another column fits. An optional measure role stays empty
  instead. A series or category role prefers a name column such as `Austria`
  over a code column such as `AT` when their names are related. An `x` axis
  keeps a month, rank or year column. Compact date formats take exactly their
  digits, and years outside 1677 to 2262 no longer crash `set_type`. (#12193)
