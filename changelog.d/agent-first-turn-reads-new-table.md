### Fixed

- **The chat's first reply to a paste describes the table that just arrived.**
  In the chat of "Use with my data", the server now puts the new table's
  columns, types, ranges, a few cells and the bindings in front of the
  assistant itself on the first turn after a paste, the data summary or the
  note typed with the data, as the profile tool returns them and fenced as
  data, so that turn describes this table also when the assistant does not
  call the tool. When the paste replaced earlier data, the assistant is also
  told that nothing said before that turn describes the new table. Before,
  only a call of the tool showed it the table, and the call was sometimes
  skipped: with a second table whose `day` column held text where the first
  had dates, the assistant answered a note from its summary of the first
  table and said the column already read as dates.
