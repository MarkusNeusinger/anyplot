### Added

- **Text operations in the data step.** `prepare_data` takes four more
  operations with literal texts only, never a pattern: `split` a column at a
  separator into 2 to 10 new columns (`10–25` gives 10 and 25; a leading
  minus stays a sign), `extract` only the number, the digits or the letters of
  each cell, `strip` a prefix or a suffix, and `replace` a text. Each writes
  new columns beside its source, typed as `set_type` reads them (the dataset's
  decimal mark, its thousands rules, at most a tenth of failing cells, which
  the change line counts), and the steps chain in one call, so a column of
  ranges no longer sends the user to a spreadsheet. (#12556)
- **A column of ranges fills a lower and upper bound pair left open.** When
  `min_value` and `max_value` (or `ci_lower` and `ci_upper`, `low` and `high`)
  have no columns and a text column holds two numbers around one dash in every
  cell, the first never above the second, the session block lists its `split`
  as a certain conversion, and the service binds the two new columns to the
  pair. ISO dates, negative numbers, decimal commas, thousands separators, ids
  and spans of years keep their reading. (#12556)

### Fixed

- **The default bindings no longer invert a range.** A lower and upper bound
  pair is never bound by default to two columns whose lower one starts above
  the largest value of the upper one, where every row's minimum would lie
  above its maximum; the pair stays open, so the conversion check runs. Bound
  so by hand, the pair carries a binding warning. (#12556)
