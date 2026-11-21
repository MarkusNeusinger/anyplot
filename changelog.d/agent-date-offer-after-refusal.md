### Fixed

- **The chat no longer turns your dates into numbers to fill an axis by
  itself.** In the chat of "Use with my data", the assistant sometimes put a
  date column on an axis that takes numbers, such as a scatter plot's x, was
  refused, and then added the dates as a decimal year or as days since the
  first date, which nobody had asked for. Which numbers a date becomes is your
  choice. Now that refusal says so, and in the same turn the server makes no
  such column and no row numbers; the reply can offer them instead. When you
  ask for the days or the year yourself, the assistant makes them first and
  binds them after, as before. (#13757)
