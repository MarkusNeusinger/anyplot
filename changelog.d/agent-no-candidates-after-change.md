### Fixed

- **No row numbers nobody asked for after a data change.** Once the
  assistant has changed the data in a turn, the session block no longer
  lists the conversion candidates for an open role for the rest of that
  turn. Recomputed on the new version, the row-number fallback reappeared
  as a certain line, and a chain of a drop, an aggregate and a sort gained a
  `row_number` column in about half the prep-eval runs. The conversions the
  server made stay listed, and the next turn lists the candidates again.
  (#12599)
