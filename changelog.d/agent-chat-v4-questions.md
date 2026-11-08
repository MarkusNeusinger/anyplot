### Added

- **Questions in the agent chat are a turn kind of their own.** A typed
  message that changed nothing gets a small `?` beside its bubble, and its
  reply starts with `? answer · nothing changed`; the chapter line counts its
  questions (`# data · 2 questions`), a button that moves the focus to each in
  turn with a short green highlight. "Nothing changed" has to hold by the
  server's word (`done.turn`, new on the page) and by what the turn's stream
  showed, so a plot, a data version, a switch or a chosen language always wins
  over the server's `answer`, a wish kept for the first plot never reads as a
  question, and the memory read after the turn still vetoes. The note typed
  with an attachment is never one: its reply summarizes the data that just
  came. (#12826)
- **A plot card counts the remembered decisions it kept.** Its label reads
  `plot v4 · seaborn · kept 3` in place of the request, and the open card's
  first line names them, `kept: y = 7 line · x label · new: log scale on y`
  (only `new: …` on a phone), from the ids the server sends with each version
  (`plot.memory`). The texts stay with the version, so a later `.forget()`
  never rewrites an older card, and a version whose memory the server did not
  name shows no `kept` at all, never `kept 0`. (#12826)

### Changed

- **The remembered decisions moved from above the composer to the latest
  `# plot` line.** `3 decisions ▾` there unfolds their list under the line,
  each with `.forget()`, then `.forget_all()` and the ⓘ, as the v4 design
  draws it; the `# remembered` heading with `.hide()` and `.show()` is gone.
  The list moves with its open state and the focus when a newer plot chapter
  opens, and a removal is still announced outside the thread's log. (#12826)
