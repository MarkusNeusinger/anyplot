### Added

- **The assistant derives a category column from your data.** The new `prepare_data`
  operation `classify` adds a text column whose cells are labels, chosen per row by
  the first of up to ten rules whose conditions hold: two classes ("y above 0 is
  class 1, the rest class 2") or levels ("above 70 high, above 40 medium, else
  low"), so a table of numbers gets a column for a text role such as a
  feature or a category. The conditions are the ones `drop_rows` uses, compared and
  never evaluated; labels are at most 40 characters and stay text in every later
  version. The prep eval gains a case for each.
