### Changed

- **The generator checks its own picture with the review's questions before
  it commits.** Step 4 of the generation prompt asked five questions about the
  palette and the theme; the review then deducted for things the generator was
  never asked to look at. Now it opens both renders and asks of each whether
  every required `A good version shows:` bullet of the spec is in the picture
  (with the spec's own conditions), whether the palette follows the Imprint
  order and ramps (ordered categories and semantic colors excepted, as in the
  review) without resting on red against green, whether text reads at a size
  that fits it, whether the plot uses the canvas, whether everything stays
  whole and clear of overlap, whether text on marks reads, whether legend
  glyphs match the marks and the legend speaks to a reader, whether every
  series stands out on the dark page with markers that suit their number, and
  whether the axis titles carry units. Every question reads "yes" for a clean
  plot. A "no" is fixed in one round of its own, never by deleting an element,
  and the commit body records the result in a `Visual self-check:` line, so the
  next regeneration run can measure how much it catches. (#14240)
