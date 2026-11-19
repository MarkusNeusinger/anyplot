### Fixed

- **The chat's first reply to a paste reads the table that just arrived.** In
  the chat of "Use with my data", the server now hands the assistant the new
  table's columns, types, ranges, a few cells and the bindings on the first
  turn after a paste, the data summary or the note typed with the data, as
  the profile tool would return them and fenced as data. When the paste
  replaced earlier data, the assistant is also told that nothing said before
  that turn describes the new table. Before, it had to call the tool for the
  description and sometimes did not: with a second table whose `day` column
  held text where the first had dates, it answered a note from its summary
  of the first table and said the column already read as dates. A data
  summary now takes one model call instead of two.
