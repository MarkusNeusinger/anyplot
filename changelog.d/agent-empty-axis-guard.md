### Fixed

- **The chat no longer fills an emptied plot axis with a column nobody asked
  for.** After a change of the data that took an axis's column (the daily mean
  per sensor drops the humidity of a scatter plot's y), the assistant added the
  timestamps as days since the first date and put them on the chart. In such a
  turn the server now refuses to turn a date into numbers or to make row
  numbers, or to bind such a column, whichever call tries it, and the refusal
  costs none of the turn's two data steps. The table keeps only what was asked
  for, the reply names the axis that lost its column, the plot waits, and the
  next turn lists what the server can compute for it. A column the request
  derives or converts from text itself still takes the axis it names.
- **A plot selection that hides no row any more is cleared.** After "keep only
  these rows in the table", the old selection stayed in force on the plot. A
  change of the table now clears every selection that keeps all of its rows,
  however the change was written, with a line that says so; a top N stays, as
  it still orders the rows.
- **An undo also takes back what the step did to the plot's view.** Undoing
  "keep only these rows in the table" or an `apply_view` brought the table back
  but drew every row. The view from before the step now comes back with it, as
  long as the view in force is still the one the step left.
- **Two prep eval cases no longer fail correct answers.**
  `en-code-strip-plot-calls` adds seeded noise, so it needs the code tool
  again; `de-klasse-aus-vorzeichen` accepts the labels `1` and `2` beside
  `Klasse 1` and `Klasse 2`, through a new `also_accepted` field for a request
  with two fair readings.
