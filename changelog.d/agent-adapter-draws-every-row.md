### Changed

- **The plot code draws every row it gets, in all four languages.** The shared adapter rule no longer lets
  the plot code group, pivot or filter the user's rows: it splits them into series and groups, computes the
  statistic its plot type draws (quartiles, bins, a density, a fit) and the computed roles, but never filters
  by a value, cuts to the first or largest rows, samples, drops duplicates or averages the rows of one key.
  A change request, an earlier request or a plot-memory decision that asks for such a change is left out with
  one note, and the assistant offers it as a data step with counts and an undo, and sends such wishes to the
  data step from then on. The random draws stay for jitter only. In the persona round of 2026-11-06 a line
  chart averaged 27 measurements to 9 points in its code without a count.
- **The assistant names rows the plot draws no mark for.** The server's "The plot draws no mark where a value
  is missing" line is named in every reply to that plot, as what the plot draws and never as rows removed
  from the data, and stays on the list of notices that a short reply keeps.
- **Eval cases can take data steps before the plot.** A matrix case's `before_operations` are stored as the
  session's next data versions through the server's own code, with no model call. The 45 `n5000` cases of
  `bar-grouped`, `heatmap-basic` and `pie-basic` use it for the aggregate the assistant offers on their
  repeated keys, since their plot code no longer aggregates the raw records itself.
