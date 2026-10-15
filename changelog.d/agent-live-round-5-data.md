### Added

- **Daily, weekly and hourly buckets for `prepare_data` aggregates.** `aggregate` takes the
  periods `hour`, `day` and `week` (ISO, each as its Monday) beside `month`, `quarter` and
  `year`, and keeps the key a datetime, so "a daily mean per sensor" over 13-minute readings
  keeps a time axis; the bucket follows the column's own UTC offset as stored, which the
  change line names. A new prep eval case covers it. (#12200)
- **A table picker for pastes with several tables.** A report sheet with two tables one below
  the other (a title, a table, a blank row, a caption, a second table) is read as its first
  table instead of one table with the second header as a data row; a warning names the others,
  and the data panel offers them in a picker that parses the same text again, as the sheet
  picker reads another sheet. (#12200)

### Fixed

- **R and pandas row names no longer become the default x.** A first column in a tool's exact
  row-name shape (R's empty header or readr's `...1` over `1` to `n`, pandas' `Unnamed: 0` over
  `0` to `n - 1`) leaves the table with a warning that counts its cells; other row-number
  columns such as R's `X` stay but take no default binding while another column fits. (#12200)
- **Missing-value tokens are announced in every column.** `NA`, `-` or `n/a` read as missing in
  a number or date column now gets the same per-column count as in a text column. (#12200)
- **Whole numbers are written without `.0`.** `87000` beside `120500.5` stays `87000` in the
  preview and in `data.csv` (it showed as `87000.0`), and `prepare_data` writes every whole
  number it moves or computes the same way; a rounded value keeps its note. (#12200)
