### Fixed

- **Dates the chat does not read no longer turn into row numbers unasked.** In
  the chat of "Use with my data", a pasted table whose day column is in a
  form the chat does not read, such as `2026/03/01`, `1st March 2026` or
  `2026-03-01 10:00:00 UTC`, got the row numbers 1 to n on the axis of a line
  plot, made without a question and without a word about the dates. Now the
  chat asks first: it names the column, says why its dates do not read, and
  lists the forms it reads. The same holds for a column with a day that does
  not exist or with slash dates whose order of day and month is not settled.
  A list of values without such a column still gets its row numbers as
  before.
