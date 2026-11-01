### Added

- **An open required role makes the server check which columns a conversion
  would fill it with.** When the bindings leave a required role open, the
  service dry-runs `set_type` on every free text column in code
  (`agents/anyplot/data/conversions.py`) and lists each candidate in the
  session block with its counts, `certain` or `uncertain` with the reason, and
  the operations. The root makes a certain conversion in the summary turn as a
  new column beside the original (`set_type` gained `name`), which the service
  binds to the role, and proposes an uncertain one as its one question; the user
  confirms as usual and `.undo()` takes it back. (#12512)

### Fixed

- **Month names with a year are dates.** The parser and `set_type` read
  `Nov 2026`, `Okt. 2026`, `2026 Nov` or `März 2026`, in the eleven languages of
  `months.py`, as the first day of each month, with a warning that counts the
  cells; a two-digit year (`Nov 26`) stays text. In the live test of 2026-11-01
  a price table of `Nov 2026` to `Dec 2025` left a time series' date role open,
  and the root asked the user for a date column. (#12512)
- **The minus sign is a minus.** A minus written `−` (U+2212) or as an en dash
  before a number reads as a sign, in the parser and in `set_type number`, with
  the cells counted; a range such as `10–20` stays text. Before, a change column
  of `+75` and `−100` stayed text. (#12512)
- **A newest-first time series is sorted, not asked about.** A date column's
  profile says which way its dates run (`order`), and the root sorts a
  newest-first date column of the plot ascending in the summary turn instead of
  asking whether to reverse the rows. (#12512)
- **`set_type` to dates no longer fills in what a cell lacks.** pandas read a
  cell without a year as the year 1 (`May`, `Nov 26`) and a time alone as
  today; such cells now fail and are counted, and a month name no longer leaves
  the day and month order open. (#12512)
