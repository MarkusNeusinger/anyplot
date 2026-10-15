### Added

- **Daily, weekly and hourly buckets for `prepare_data` aggregates.** `aggregate` takes the
  periods `hour`, `day` and `week` (ISO, each as its Monday) beside `month`, `quarter` and
  `year`, and keeps the key a datetime, so "a daily mean per sensor" over 13-minute readings
  keeps a time axis; the bucket follows the column's own UTC offset as stored, which the
  change line names. A new prep eval case covers it.
- **A table picker for pastes with several tables.** A report sheet with two tables one below
  the other (a title, a table, a blank row, a caption, a second table) is read as its first
  table instead of one table with the second header as a data row; a warning names the others,
  and the data panel offers them in a picker that parses the same text again, as the sheet
  picker reads another sheet.

### Fixed

- **R and pandas row names no longer become a column.** A first column under an empty header
  (R's `write.csv`, pandas' `to_csv`), `Unnamed: 0` or `...1` whose cells only number the rows
  `1` to `n` or `0` to `n - 1` leaves the table with a warning that counts its cells, so it is
  never bound as the default x.
- **Missing-value tokens are announced in every column.** `NA`, `-` or `n/a` read as missing in
  a number or date column now gets the same per-column count as in a text column.
- **Whole numbers keep the form they were written in.** `87000` beside `120500.5` stays `87000`
  in the preview and in `data.csv` (it showed as `87000.0`), and the `prepare_data` operations
  carry each whole number's form through a wide-to-long, a sort or a pivot.
