### Changed

- **The agent chat reads in chapters, and the data card stays open.** A `# data`
  or `# plot` line opens each stretch of the talk where it turns from the data to
  the plot and back, and a change of the data after a plot opens a new `# data`
  chapter with the card in it. The thread reads in time order (the owner's
  decisions of 2026-11-07): a change asked for in the chat puts the card right
  after the request, before the reply, and the card's own `.undo()`,
  `.to_long()` or a picker moves it to the thread's end, before and after a plot
  alike, each older version folded with its own summary under it. Every data
  version gets its
  number on the card's border (`data v3 · made long · 48 rows × 4 cols`), and
  every older version folds to that label, which opens it read-only. The page
  names a version only by that number: the card's change lines, its full view
  and the status line (`data v3 fits · 48 rows · 4 columns`) no longer show the
  server's version, which starts over with every paste. A library switch is a
  line of its own that names the decisions it keeps. The pinned header above the
  thread and its `.show()` and `.hide()` are gone: the card stays open in both
  steps. The keyboard focus follows a card that moves, and the page keeps the
  focus clear of the site's sticky masthead. (#12604)
