### Fixed

- **Four library prompts no longer pin a value the review deducts for.** A
  comparison of 298 regenerated pairs traced four recurring defects to a
  snippet in the library prompt itself. In `prompts/library/plotly.md` the top
  margin drops from `t=80` to `t=60`, which removes the empty band under the
  title on the 450 px layout; margins stay explicit. In `pygal.md` the grid
  takes `guide_stroke_color` and `major_guide_stroke_color` from `INK_MUTED`,
  because pygal ignores `foreground_subtle` for guide lines and its black
  default almost vanishes on the dark page; both tick sizes are now 44, the
  style guide's tick size, so one axis no longer shows two sizes. In
  `plotnine.md` the four-sided panel border, the legend frame and the
  page-colored key tiles are gone; the frame uses `color="none"` because
  `color=None` inherits a black outline under `theme_minimal()`. In
  `letsplot.md` the grid is INK at 15 % and the minor grid INK at 5 %, as in
  plotnine, instead of full INK; lets-plot reads the alpha from an `rgba()`
  color.
