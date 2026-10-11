### Added

- **The data field reads free text as a table, and you confirm it first.** Pasted
  text that is no table the parser can read, such as "a bar chart with dog 7, cat 3
  and bird 4" or a list typed one value per line, is read by the judge model into a
  table (column names, rows, a short note on anything ambiguous). The page shows that
  table as a preview with `.use()` and `.discard()`, and nothing is stored until you
  use it: the confirmation posts the table's CSV through the ordinary parse, pre-filter
  and judge path. Text over 4,000 characters, JSON arrays and objects, and real tables
  take the old path unchanged. (#12130)
