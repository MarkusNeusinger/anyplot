### Fixed

- **Five more library prompts no longer write a layout defect into every
  file.** A count over the 3,250 live renders of five libraries traced six
  recurring defects to a snippet in the library prompt. In
  `prompts/library/bokeh.md` the screenshot paints the browser page in the
  theme's page color, which removes the 1 px light line along the top and
  left edge of 299 of 325 dark renders, and a legend's keys grow from the
  20 px default to 40 px beside the 34pt labels. In `altair.md` the chart
  takes `autosize` fit at 800×450 (600×600), so title, axes and legend fill
  the canvas instead of a small view padded to it (70 % of altair files
  showed an empty frame); a compound chart that cannot fit is scaled down
  and padded instead of stopping the run with `SystemExit`, which had led
  sessions to a PIL `thumbnail` the chat's validator refuses. In
  `ggplot2.md` the grid is INK at 15 % and 5 % instead of solid ink, with
  no panel border and no legend frame, as the plotnine prompt already has
  it. In `letsplot.md` a fixed-aspect plot is wrapped in a one-panel
  `gggrid` and a composite takes the page color, so neither leaves
  transparent or white strips at the canvas edge. In `seaborn.md`
  `plt.tight_layout()` runs before the save, and a figure-level plot resets
  its size after the legend widened it past the canvas.
