### Fixed

- **A conversion to dates reads only a date, or a date and a time.** In the
  chat of "Use with my data", a cell converts to a date only when it is a
  date alone or a date followed by a time. A cell with anything else after
  its date is unreadable and counted, so the chat proposes or asks instead
  of guessing, and a refused conversion says how many cells hold more after
  their date than a time. At the paste, a time with an offset outside -12:00
  to +14:00 (`2026-03-01 08:00-16:30`) is no longer typed as a date and stays
  text. Before, a range such as `2026-03-01-2026-03-05` was read as 2
  March beside a notice of UTC offsets no cell held, `2026-03-01 -05:00` or
  `13.03.2026-05:00` as that day at 05:00, `2026-03-01/05` as 1 March,
  `2026-03-01 of` and `2026 of` as that day and that year, the word skipped,
  and a range of times such as `2026-03-01 9:00-17:00` as 09:00 at an offset
  of -17:00, which no place has; each was rated certain and made without
  asking. A word before the date, as in `Sunday, 1 March 2026`, still reads.
  (#13187)
- **A time without a colon keeps its hour.** Hours such as `2026-03-01T00`
  to `T03`, `2026-03-01 10am` and `2026-03-01T1000` are written with their
  time; the column of dates used to drop it, because only a colon made a
  column one of times. (#13187)
