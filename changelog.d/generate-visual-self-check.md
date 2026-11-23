### Changed

- **The generator checks its own picture with the review's questions before
  it commits.** Step 4 of the generation prompt asked five questions about the
  palette and the theme; the review then deducted for things the generator was
  never asked to look at. Now it also asks, of both renders, whether every
  `A good version shows:` bullet of the spec is in the picture, whether the
  plot uses the canvas, whether anything is cut off or overlaps, whether text
  on marks and legend glyphs read, whether every series stands out on the dark
  page, and whether the axis titles carry units. A "no" is fixed in at most
  two rounds of its own, never by deleting an element, and the commit body
  records the result in a `Visual self-check:` line, so the next regeneration
  run can measure how much it catches.
