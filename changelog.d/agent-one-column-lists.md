### Fixed

- **A pasted or dropped list of numbers is a table, not free text for the model.** One
  column of integers, numbers, dates or booleans (live round 7: a header and 800 commute
  times, the input of a histogram) went to the transcriber, which timed out every time
  and showed "unavailable right now"; it is now stored like any table, as are digit codes
  such as postal codes and a column of repeating categories under a header (with a short
  note naming the line read as the column name when that line looks like a category). A list without a header line
  keeps its first value as the first row, in a column named `value`, with a warning. The
  transcriber takes at most 200 lines besides its 4,000 characters, and free text past
  them is refused with that limit as its cause instead of being stored as it parsed. A
  reading cut off at its cap, or out of time on a text near those limits, is
  `422 unparseable` with a cause that names the text's lines and characters and asks for
  a separator; a short text that times out, an error or a quota stays
  `503 guard_unavailable`. (#12202)
