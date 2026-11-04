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
  open. (#12558)
- **An open number role offers a free date column.** When a required role
  that takes numbers only stays open and a date column is free, the session
  block lists `date_number` as an offer, never made unasked: the unit is the
  user's choice, so the assistant names it in one statement, and a request
  without a unit takes the days since the first date. (#12558)

### Changed

- **The prep eval counts a closing invitation as a reply miss.** A reply whose
  last sentence or clause asks the user to choose ("Choose …", "Pick one …",
  "tell me which …", "Wähle …") misses on the same terms as a closing
  question, and an open role the session block offered a date column for no
  longer excuses either. On the earlier wording 2 of 5 summary replies of the
  owner's case closed so; on the final one, 0 of 6. (#12558)
