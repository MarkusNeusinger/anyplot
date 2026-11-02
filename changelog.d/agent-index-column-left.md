### Changed

- **The row numbers lead the data and the data view.** The `row_number`
  operation inserts its column (`index` by default) as the first column instead
  of the last, and moves a reused row-number column there; the change line says
  so, and no value or row moves. The data view shows a column that numbers the
  rows (the operation's `index`, or a pasted `X`, `Unnamed: 0` or `column_<n>`)
  leftmost in place of its own `#` counter, with the data's own values, also
  after a sort reordered them; without such a column the counter stays. A sorted
  column's header keeps room for its dtype beside the sort arrow and the menu.
  (#12521)
