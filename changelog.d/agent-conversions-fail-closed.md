### Fixed

- **A data conversion in the chat no longer loses a digit.** A count written
  with thousands dots and a footnote mark (`38.790*`) came out as 3879: taking
  the mark off made a new column that was typed at once as the number 38.79,
  and removing the dot from that number's stored text dropped the zero. A new
  column of `strip`, `replace` or `split` whose decimal mark could as well
  separate thousands now stays text until `set_type` reads it with the mark
  the user names. A text operation reads a pasted number column from its cells
  as pasted, and is refused on the `.` or `,` of any other number column.
  `set_type` with a decimal comma on a number column it cannot read again is
  refused, where it answered "nothing changed" and the call went on to compute
  with the wrong reading and store it. Without a named mark, `set_type` says
  in its change line which mark it took when the cells read with either.
  (#13056)
