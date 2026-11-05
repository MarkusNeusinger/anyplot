### Changed

- **The server makes a paste's certain conversions for open roles.** On the
  summary turn of a paste (the summary action, or the note sent with it), the
  server applies the operations of every `certain` line of "Conversions for
  open roles" itself before the assistant's first call: a column of years
  read as dates, prices read as numbers, a column of ranges split into its two
  bounds, or the row numbers on an open axis. They land in one data version of
  their own, so one `.undo()` takes back exactly these conversions, and the
  original columns stay. The assistant names each in the summary with its count
  and the new column's name, and never repeats or drops one. The conversions
  run behind the scope guard, so a refused note changes nothing. `uncertain`
  lines stay the assistant's one question, a `date_number` offer still waits
  for the user's request, and a later turn never makes a line by itself. The
  assistant used to make these lines with its own `prepare_data` call, and the
  prep eval's `en-note-rename-year-column` failed 3 of 3 runs: the date column
  was skipped, or made and dropped again. Now it passes 3 of 3, with the
  summary's row count and the conversion in every reply.
- **The summary turn stays the summary after the assistant changes the
  data.** The session block's "pasted just now" line now holds for every model
  call of that turn. Before, the reply after the assistant's own `prepare_data`
  lost the line and answered the note without the summary.
