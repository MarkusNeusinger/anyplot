### Added

- **Dates as numbers in the data step.** `prepare_data` takes a `date_number`
  operation that adds a number column beside a date column: the calendar
  year, the whole days since the column's earliest date, the Unix time in
  seconds (UTC, with the change line saying how a date without a time and a
  time without an offset were read), or a decimal year. A missing date stays
  empty, the change line counts the dates and the empty cells, the new column
  fills an open role that takes numbers, and `.undo()` takes it back. It came
  from the owner's test of a customers table on `scatter-basic`, where
  "convert subscription date to integer" had no operation and `y` stayed
  open.
- **An open number role offers a free date column.** When a required role
  that takes numbers only stays open and a date column is free, the session
  block lists `date_number` as an offer, never made unasked: the unit is the
  user's choice, so the assistant names it in one statement, and a request
  without a unit takes the days since the first date.
