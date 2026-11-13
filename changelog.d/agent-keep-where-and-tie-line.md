### Added

- **"Only these rows" has a form of its own.** In the chat of "Use with my
  data", a selection could only be said backwards: the assistant dropped
  every row that was not wanted, so "only rent and electricity" had no form
  at all, and one wrong negation was a silently wrong selection. The data
  step now keeps the rows you name: some categories, a period from its
  first to its last day, or everything at least or at most a value (`ge`
  and `le` are new comparisons). The change line counts both sides and says
  how many of the dropped rows had no value to test, which the count alone
  would hide. This is the engine step before views of the plot.

### Changed

- **A top N says when its cut falls among equal values.** "The top 2 by
  revenue" used to cut silently through three cities with the same
  revenue: which of them stayed was the order they had before the sort.
  The cut still falls at N, and the change line now names the tied rows on
  each side, so the assistant can say so and offer more rows.
- **A date without a time means the whole day.** "Until 31 January" now
  takes in every row of the 31st whatever its time, and "after 31 January"
  none of them. Before, "after" took the day's rows past midnight in.
