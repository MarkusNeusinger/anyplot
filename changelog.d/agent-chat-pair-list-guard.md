### Fixed

- **A change request in words no longer replaces the data.** Since #13019, a
  short request with two "label number" parts, such as `x bis 2030, y bis 60`
  or `Titel 2026, Schrift 14`, routed as a list of pairs. It replaced the
  user's table with two `label`/`value` rows, and there is no `.undo()` back.
  Text with a word of a plot wish (`bis`, `max`, `Titel`, `Linie`, `Schrift`,
  `ticks` and more) is now never a pair list, on the page and in the server's
  reader, which share one word list (`wishWords.json`, pinned by a test). An
  axis letter alone is no label either. While the session holds data, a list
  needs three pairs; on a fresh page two still count (`Apples 7, Pears 12`).
  A table typed into the box over data now gets the same "replaces your data
  (N rows, no .undo())" line as an attachment before it goes. (#13035)
