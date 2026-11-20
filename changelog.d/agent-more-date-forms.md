### Changed

- **The chat reads four more date forms, the ones widely used tools write.**
  In the chat of "Use with my data", the paste types these as dates, and a
  conversion to dates without a format reads them too: a time followed by
  `UTC`, as BigQuery exports write it (`2026-03-01 10:00:00 UTC`), the same
  moment as `Z`; a UTC offset after a space, as git and Ruby write it
  (`2026-03-01 10:00:00 +0100`, also `+01:00`); a 12-hour clock with AM or
  PM, as US Excel writes it (`3/15/2026 10:00:00 AM`), where `12:00 AM` is
  midnight; and a date with the year first and slashes (`2026/03/01`), also
  with a time. Each is read exactly, with no guess: an offset still counts
  only from −12:00 to +14:00, and the clock settles no order of day and
  month, so slash dates whose days are all 12 or less are still read day
  first with a note that says it is a guess. Before, the paste kept such a
  column as text, and for an axis that takes dates the chat asked whether to
  number the rows instead. Zone names such as `GMT`, a comma after the year,
  weekdays and ordinals stay outside the list.
