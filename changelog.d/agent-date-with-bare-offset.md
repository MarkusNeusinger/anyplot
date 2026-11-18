### Fixed

- **A date with a UTC offset and no time stays as written.** In the chat of
  "Use with my data", a pasted column such as `2026-03-01-05:00` or
  `2026-03-01+01:00` now stays text with a note that names its shape. On
  request the days go into a new column, and the change line counts the
  dropped offsets ("3 dates had the UTC offset -05:00, which was dropped; the
  days are as written"); for an open date role the chat asks first. Before,
  an offset west of UTC was read as a time of day (`-05:00` as 05:00) and the
  conversion was made without asking, an offset east of UTC failed without a
  reason, and as a filter bound `2026-03-01+01:00` meant 01:00 and left rows of
  1 March out; such a bound now means the whole day. A filter by date on the
  pasted column itself, which would compare the text and cut the rows of one
  day in two, is refused with the way out: the converted column.
- **Hour labels written `YYYY-MM-DD-HH` are no longer read as dates.** A date
  followed by a sign and digits in no offset form is refused, with the form
  the column needs, when it is converted or used as a filter bound. Before,
  four hour labels became four equal dates, and the chat made that conversion
  without asking.
