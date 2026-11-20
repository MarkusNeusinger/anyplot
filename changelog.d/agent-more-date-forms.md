### Changed

- **The chat reads four more date forms, the ones widely used tools write.**
  In the chat of "Use with my data", the paste types these as dates, and a
  conversion to dates without a format reads them too: a time followed by
  `UTC`, as BigQuery exports write it (`2026-03-01 10:00:00 UTC`), the same
  moment as `Z`; a UTC offset after a space, as git and Ruby write it
  (`2026-03-01 10:00:00 +0100`, also `+01:00`); a 12-hour clock with AM or
  PM, as US Excel writes it (`3/15/2026 10:00:00 AM`), where `12:00 AM` is
  midnight; and a date with the year first and slashes (`2026/03/01`), also
  with a time. The zone, the clock and the year-first date are read exactly
  as written, and an offset still counts only from −12:00 to +14:00. Plain
  slash dates whose days are all 12 or less keep an older rule and are read
  day first, with a note that says it is a guess; a column of slash dates
  with a 12-hour clock is not read by a guess: the chat asks which order is
  meant, and a format of `MM/DD/YYYY` or `DD/MM/YYYY` reads it. Before, the
  paste kept a column in any of the four forms as text, and for an axis that
  takes dates the chat asked whether to number the rows instead. Zone names such as `GMT`, a comma after the year,
  weekdays and ordinals stay outside the list. (#13278)
