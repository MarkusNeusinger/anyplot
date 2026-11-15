### Added

- **The chat's page says which rows a plot draws, and `.show_all()` brings
  the rest back.** In "Use with my data", a plot that shows only some of
  your rows ("only 2024", "the top 10 by revenue") now says so on its card
  (`draws 10 of 248 rows · Jahr = 2024 · top 10 by Umsatz`), and the data
  card says under its bindings that the plot draws 10 of its 248 rows, so
  the table and the plot no longer seem to disagree. `.show_all()` on the
  newest plot clears the view and draws every row again, without a new
  data version and without typing; the result names the rows that are
  back. Before, the view stood only in the plot's list of changes.
