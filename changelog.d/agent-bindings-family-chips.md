### Changed

- **A series family's columns are chips in one row.** The `y` of line-multi,
  area-stacked and every other spec with a variadic family had one dropdown per
  series plus an empty one for the next, so eight series made nine rows. Now
  each bound column is a chip with a `×` that removes it, followed by `+ y ▾`, a
  menu of the columns left. Columns the role cannot take stay in the menu,
  greyed out with the reason. The row keeps its name and kinds, wraps at a
  phone's width under the role's name, and keeps the keyboard in the row after a
  change. The server still gets `y1` to `yn`. (#12580)
