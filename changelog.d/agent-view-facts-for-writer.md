### Fixed

- **The models that write and review a plot hear which rows a view
  draws.** In "Use with my data", a plot that draws only some of your rows
  ("only the first quarter") computes its figures from those rows, but a
  total or a mean in its title, an annotation or the legend could read as
  the whole table's, and the chat described it that way. The model that
  writes the plot code is now told how many of the table's rows the plot
  draws and which selection, and is asked to name that selection in the
  label of such a figure ("Total of the first quarter") and to stop naming
  that selection once you show every row again, except in words you wrote
  yourself. The model that reviews the render is told the same and asked
  to count such a figure whose label reads as the whole table's as a
  defect. The chat is told that a total, a mean or a count the plot draws
  covers only the rows it draws, and asking for a version's code also says
  how many rows its `data.csv` (and a JavaScript plot's `plot.html`) holds
  and which view it drew.
- **A cell with a line break counts as one row.** In "Use with my data",
  the render check that compares the points a plot draws with its rows
  counted the lines of `data.csv`, so a quoted cell over two lines, as a
  cell pasted from a spreadsheet can hold, counted as two rows. That check
  now counts the table's rows, and so do the same check when you switch
  the theme of a plot and the row count the chat reports for a version's
  data.
