### Changed

- **The agent chat reads in chapters, and the data card stays open.** A `# data`
  or `# plot` line opens each stretch of the talk where it turns from the data to
  the plot and back, and a change of the data after a plot opens a new `# data`
  chapter at the thread's end with the card in it, also when the card's own
  `.undo()`, `.to_long()` or a picker made the change (the owner's decision of
  2026-11-07, so the thread reads in time order). Every data version gets its
  number on the card's border (`data v3 · made long · 48 rows × 4 cols`), and
  every older version folds to that label, which opens it read-only. The page
  names a version only by that number: the card's change lines, its full view
  and the status line (`data v3 fits · 48 rows · 4 columns`) no longer show the
  server's version, which starts over with every paste. A library switch is a
  line of its own that names the decisions it keeps. The pinned header above the
  thread and its `.show()` and `.hide()` are gone: the card stays open in both
  steps. The keyboard focus follows a card that moves, and the page keeps the
  focus clear of the site's sticky masthead. (#12604)
