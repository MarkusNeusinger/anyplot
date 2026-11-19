### Changed

- **Dates are read in a short list of forms, the same at the paste and on
  request.** In the chat of "Use with my data", a conversion of a text column
  to dates without a format now reads only the forms the paste reads:
  `2026-03-01`, also with a time, seconds, a fraction and a UTC offset;
  `01.03.2026`; `03/15/2026` or `15/03/2026`, with the order of day and month
  decided once for the whole column; a day with a month name and a year
  (`8 Nov 2026`, `1. März 2026`, `March 1, 2026`), each also with a time; and
  months such as `2026-03` or `Mar 2026`. Each cell reads in its own form, so
  ISO dates beside `11 Mar 2026` all convert; a slash date beside other forms
  reads only in an order the column's slash dates settle, never by guess. A
  cell in any other form is not read, and the chat says why: a day that does
  not exist, slash dates that settle no single order of day and month, or,
  for a form outside the list, the forms it reads ("the chat reads
  2026-03-01, 01.03.2026, 03/15/2026, 8 Nov 2026, each also with a time, and
  months such as 2026-03 or Mar 2026"). A format such as `YYYYMMDD` or
  `MM/YYYY` still reads its own
  form on request, and a form no format names, such as `1st March 2026` or
  `2026/03/01`, is read by no conversion now. Before, a general reader
  guessed the format cell by cell: it read a range of days as its first day,
  hour labels `T00` to `T03` as one day four times, `-05:00` after a space as
  05:00, and month-first dates in one column partly day first, and the chat
  made such conversions without asking.

- **A pasted column of days with a month name is a date column.** `8 Nov 2026`,
  `1. März 2026` or `March 1, 2026` (also `Mar 1 2026`), in the eleven
  languages of the chat's month names, are typed as dates at the paste, with
  a note that counts them, and so is an ISO time with a lowercase `t` or `z`
  (`2026-03-01t10:00z`); a headerless list of such dates is one date column,
  and a no-break space inside a date reads as a plain one. Before, such a
  column stayed text, and for an open date role the chat made a conversion
  into a new column first.

### Fixed

- **A UTC offset counts only from −12:00 to +14:00.** A pasted
  `2026-03-01 08:00-16:30` is no longer typed as a time at an offset of
  −16:30, and a date followed by `-17:00` is no date with an offset, at the
  paste, in a conversion and as a filter bound.
