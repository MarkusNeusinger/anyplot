### Added

- **The chat rebuilds from your original table.** `prepare_data` and
  `query_data` take `from_version`: the current version (the default), the
  original table as pasted or opened, or a version number the session block
  lists with the change that made it. "The first 20 after all" after a top
  10 is one call from the original, stored as the next version on top, and
  its first change line says where it started ("from your original table:
  kept the first 20 of 487 rows"); a question reads the pace per run after
  a weekly sum the same way. The history is never rewritten, the user
  confirms the new data, and `.undo()` stays one step back. The original
  stays in the store past the five-version undo history, and a version of
  data a new paste replaced is refused with a closed code (`other_paste`).
  It came from the persona tests of 2026-11-06, where the chat sent users to
  `.undo()` or a new paste three times.
