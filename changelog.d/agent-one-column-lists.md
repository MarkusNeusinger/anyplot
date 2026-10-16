### Fixed

- **A pasted or dropped list of numbers is a table, not free text for the model.** One
  column of integers, numbers, dates or booleans (live round 7: a header and 800 commute
  times, the input of a histogram) went to the transcriber, which timed out every time
  and showed "unavailable right now"; it is now stored like any table, as is a column of
  repeating categories under a header. A list without a header line keeps its first value
  as the first row, in a column named `value`, with a warning. The transcriber takes at
  most 201 lines besides its 4,000 characters, and a reading that runs out of time or
  output room is `422 unparseable` with a cause that names the text's lines and characters
  and asks for a separator; only an error, a quota or an unparseable answer stays
  `503 guard_unavailable`.
