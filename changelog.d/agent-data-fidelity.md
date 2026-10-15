### Fixed

- **Pasted data keeps every digit, or a warning says what changed.** Owner rule of
  2026-10-15: precision is never lost silently. The exported `plot.py` and the render
  read `data.csv` with `float_precision="round_trip"` (pandas' default reader had
  misread about one in four 17-digit numbers); a number with more digits than a float
  holds, from CSV, JSON or a Python literal, is stored rounded with a warning that
  counts the cells; whole numbers past the 64-bit range stay text; a text cell that
  lost surrounding spaces or became missing (`None`, `-`), and NFC composition, are
  counted in warnings; the profile's integer `min` and `max` are exact (#12196).
- **Data operations no longer round or wrap numbers without a word.** `set_type number`
  reads whole numbers exactly; an `aggregate` sum of whole numbers no longer wraps
  around past 2^63; `cumsum`, row sums and differences stay whole; `pivot_longer`
  counts the whole numbers its shared column rounds. Date-times keep their fraction of a
  second and their UTC offset, a year-first time such as `2024-06-01T13:00:00Z` is no
  longer read as 6 January, and a column with different UTC offsets is refused instead
  of crashing the operation (#12196).
