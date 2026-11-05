### Fixed

- **A request to read a column as numbers converts that column.** When the
  session block lists a conversion for an open role on the column the user
  names ("read Anteil as numbers"), the assistant now reads the column itself
  as numbers or dates, instead of copying the line's new column beside it. The
  new column is only for a conversion nobody asked for, such as the ones the
  server makes on a paste. In the prep eval, `de-percent-not-count` and
  `en-percent-unit-mixed` went from 1 of 10 on `main` to 10 of 10, and the full
  set to 83 of 85.
