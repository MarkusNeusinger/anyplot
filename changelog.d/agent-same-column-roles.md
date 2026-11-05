### Changed

- **One column can play several roles in the data step.** Some plots need the
  same variable twice: the y and the size of a bubble, the value and the colour
  of a bar, a value and its label, a treemap's size and colour. A column you
  bind by hand in the data panel, or that the assistant binds on your request,
  now keeps every role it serves: picking it for a second role no longer
  clears the first, and the binding check accepts it with no warning. The
  adapter prompt tells the plot code to select such a column once and use it
  for both roles, since a table with the same column twice breaks pandas. The
  default bindings and the automatic conversions still give each column one
  role, and inside a numbered series family (`y1`, `y2`, ...) a column stays
  once, because the same series twice is never meant.
