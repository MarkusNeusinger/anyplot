### Added

- **An open required role makes the server check which columns a conversion
  would fill it with.** When the bindings leave a required role open, the
  service dry-runs `set_type` on every free text column in code
  (`agents/anyplot/data/conversions.py`), and on a whole-number column with a
  year header, and lists each candidate in the session block with its counts,
  `certain` or `uncertain` with the reason, and the operations. The root makes a
  certain conversion in the summary turn as a new column beside the original
  (`set_type` gained `name`), which the service binds to the role, and proposes
  an uncertain one as its one question; the user confirms as usual and `.undo()`
  takes it back. Ids, codes and spans of years stay out of it. The source column
  leaves the optional roles, so `Month` on `series` never splits the plot into
  one series per row. (#12512)
- **A plot without an x column draws by row number.** The new `row_number`
  operation adds a column `index` of 1 to n. When a required axis has no column
  and no conversion, the root makes it without a question, the axis takes it, and
  a number column that sat on the axis moves to the open measure: a pasted
  `1,3,5,4,6,2` ships as a line plot. A bar chart without labels gets the row
  numbers as a question, never by itself. (#12512)
- **The prep eval fails a skipped conversion, and `chat_turn` reports the
  outcome.** A summary turn that skips a `certain` conversion is a miss and fails
  the run. `chat_turn.conversion` is one closed value: `none`, `date`, `number`,
  `index` or `asked`. (#12512)

### Fixed

- **Month names with a year are dates.** The parser and `set_type` read
  `Nov 2026`, `Okt. 2026`, `2026 Nov` or `März 2026`, in the eleven languages of
  `months.py`, as the first day of each month, with a warning that counts the
  cells; a two-digit year (`Nov 26`) stays text. In the live test of 2026-11-01
  a price table of `Nov 2026` to `Dec 2025` left a time series' date role open,
  and the root asked the user for a date column. A plot writes such a column as
  months, also as a bar chart's labels and past 60 of them. (#12512)
- **A copied web table keeps its last row and loses its button.** A short line
  between the rows that holds text in the value columns (`Show 36 earlier
  months`) is left out with a count, and a last row that lost its empty cells
  stays a row. Before, the button stayed a row of empty cells, the month column
  stayed text and the last month was lost as a footer. (#12512)
- **The minus sign is a minus.** A minus written `−` (U+2212) before a number
  reads as a sign, in the parser and in `set_type number`, with the cells
  counted. An en dash stays text, as a range such as `10–20` does, and
  `set_type` no longer takes a dash for a unit, which dropped the sign of `–5`.
  Before, a change column of `+75` and `−100` stayed text. (#12512)
- **A newest-first time series is sorted, not asked about.** A date column's
  profile says which way its dates run (`order`), and the root sorts a
  newest-first date column of the plot ascending in the summary turn instead of
  asking whether to reverse the rows. (#12512)
- **`set_type` to dates no longer fills in what a cell lacks.** pandas read a
  cell without a year as the year 1 (`May`, `Nov 26`) and a time alone as
  today; such cells now fail and are counted, and a month name no longer leaves
  the day and month order open. (#12512)
