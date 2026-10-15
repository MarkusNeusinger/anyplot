### Added

- **Excel, OpenDocument, Parquet, Feather, Arrow and NumPy files go into the agent chat's data box.**
  A dropped, chosen or pasted binary file (at most 5 MB) goes to the new
  `POST .../dataset/convert` route, which reads it in the renderer's sandbox
  (`harness.py --convert`, the guard armed after the readers are loaded) and
  answers the text the paste box takes; nothing is stored, and the user's
  `.parse()` sends the text through the ordinary paste route with the file name
  and sheet as `source`. The format comes from the first bytes: workbooks
  through calamine, which reads stored values only (no formula, link or macro
  runs; a formula without a saved value is empty and counted, a sheet of only
  such formulas is refused with "open it in Excel and save it once"), Parquet
  and Arrow through pyarrow (row groups counted first, at most 20,001 rows
  read; slimmed in the image from 163 MB to 99 MB), NumPy with
  `allow_pickle=False`; every zip is checked from its directory and inflated to
  prove its declared sizes, an xlsx sheet's cell span is measured before it is
  loaded, an encrypted workbook gets "remove the password", and pickle, joblib
  and HDF5 are never read. Values keep their precision: timestamps every
  fraction digit and their offset, decimals and 64-bit integers exactly, and
  dropped columns (durations, intervals, binary) are named. A sheet comes as
  its raw cell grid, so a title above the header stays a note; a workbook with
  several sheets gets a sheet picker (empty sheets left out) that reads the
  chosen one again; a table with list columns comes as JSON records, which the
  parser expands into one row per value. Over a cap (20,000 rows, 50 columns,
  1 MB of text) the file is refused with its numbers. Conversions have their own
  limits (5 a minute, 30 a day per user, one at a time, 10 s) and wait behind
  every pipeline render. (#12194)
- **The data parser reads ISO timestamps with fractions and UTC offsets as datetimes.**
  Up to nine fraction digits and an offset (`Z`, `+01`, `+0100`, `+01:00`) are
  kept as written, so the plot's loader reads the column as zone-aware
  timestamps with full precision; a column with several offsets is written in
  UTC with a note, and `prepare_data` keeps fractions and offsets through its
  changes. (#12194)
