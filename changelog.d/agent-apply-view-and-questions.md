### Added

- **A view of the plot can be put into the table in one step.** In the chat
  of "Use with my data", "make that permanent" or "sum these per month"
  after "only 2024" now works on the rows the plot shows: the table takes
  the view's rows as a new version you check, and the change builds on
  them. Before, a change of the table read every row, so the sum added the
  rows the view had left out, and the view was dropped without a word.
  (#13101)
- **An answer says which rows it read.** While a view is set, a question
  about the data ("what do these add up to?") can be asked of the rows the
  plot shows, and the answer says whether it covers those rows or the
  whole table. (#13101)

### Fixed

- **"Which 3 are largest" names a tie.** When the cut of an answer falls
  among rows with the same value, the chat names the rows it left out
  instead of presenting the first three as the only ones. (#13101)
