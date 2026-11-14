### Added

- **A selection or a top N is a view of the plot now, and your table stays
  as you pasted it.** In the chat of "Use with my data", "only 2024", "just
  Bern and Zürich" or "the top 10 by revenue" used to cut the data table:
  every tweak was a new data version to confirm, and "the top 15 after all"
  meant going back to an earlier one. They now set which rows the plot
  draws. The table keeps every row, nothing has to be confirmed again, and
  the plot is redrawn in the same turn. A new top N replaces the old one, a
  filter on the same column replaces that filter, other filters narrow
  further, and "show everything again" clears the view. The plot's notes
  say how many rows it draws and by which view, and the data file you
  download with a plot holds those rows, so the code runs on it as it ran
  here. (#13089)
- **Cleaning stays in the table, and your word decides.** Rows that are
  wrong (a total row, test entries, duplicates) are still taken out of the
  table itself, and "delete them from the table" sends a selection there
  too. (#13089)

### Changed

- **Rows that share a key are combined for the plot alone while a view is
  set.** Without a view they still become a data version you can undo.
  Under a view that version would be made of the whole table and add up
  rows the plot never draws, so the view's rows are combined for the
  picture only, after the same question whether to sum or to average.
  (#13089)
