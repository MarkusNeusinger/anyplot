### Added

- **Excel, OpenDocument, Parquet, Feather, Arrow and NumPy files go into the agent chat's data box.**
  A dropped, chosen or pasted binary file (at most 5 MB) goes to the new
  `POST .../dataset/convert` route, which reads it in the renderer's sandbox
  (`harness.py --convert`, the guard armed after the readers are loaded) and
  answers the text the paste box takes; nothing is stored, and the user's
  `.parse()` sends the text through the ordinary paste route with the file name
  and sheet as `source`. The format comes from the first bytes: workbooks
  through calamine, which reads stored values only (no formula, link or macro
  runs; a formula without a saved value is empty and counted), Parquet and Arrow
  through pyarrow (footer row count first, at most 20,001 rows read), NumPy with
  `allow_pickle=False`; every zip is checked from its directory first, an
  encrypted workbook gets "remove the password", and pickle, joblib and HDF5 are
  never read. A sheet comes as its raw cell grid, so a title above the header
  stays a note; a workbook with several sheets gets a sheet picker that reads
  the chosen one again; a table with list columns comes as JSON records, which
  the parser expands into one row per value. Over a cap (20,000 rows, 50
  columns, 1 MB of text) the file is refused with its numbers. Conversions have
  their own limits (5 a minute, 30 a day per user, one at a time, 10 s) and wait
  behind every pipeline render. (#12194)
