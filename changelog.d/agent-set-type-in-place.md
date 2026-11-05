### Fixed

- **A request to read a column as numbers converts that column.** When the
  session block lists a conversion for an open role on the column the user
  names ("read Anteil as numbers"), the assistant now reads the column itself
  as numbers or dates, instead of copying the line's new column beside it. The
  new column is only for a conversion nobody asked for, such as the ones the
  server makes on a paste. A reading that guesses (the day and month order, the
  century, the decimal mark) still gets its one question first, and a date
  column's offer stays a `date_number`. A column read in place fills the open
  role that waits for it, exactly as the named conversion did, and never takes
  a role that is already bound. In the prep eval, `de-percent-not-count` and
  `en-percent-unit-mixed` went from 1 of 10 runs on `main` to 10 of 10, and
  the full set scored 83 of 85. (#12582)
