### Changed

- **The data card stands in the thread after its paste.** A sent attachment is the user's line in the
  agent chat's thread, as its chip named it (`▤ table · 4 lines · 46 B`), and the data card follows it,
  with the summary below. A later paste gets its line and a card of its own, and the card it replaced
  stays as a line with its shape (`# earlier data · 2 rows · 2 columns · replaced below`). A table read
  from text waits in a card at its paste: `.use()` makes it the data card, `.discard()` a
  `# table discarded` line. A change to the data, an undo, `.to_long()` and the table and sheet pickers
  update the card where it is. Once the data is confirmed, the header pinned above the thread leads to
  the card: `.show()` opens it at its place and scrolls there, `.hide()` goes back. (#12570)
- **The loader of a running turn keeps its place.** The thread's in-progress line (`working on your
  message`) is laid out as the progress timeline is, the loader first and the words beside it (on a phone
  below it), so when a typed change reaches its first pipeline step and the timeline takes over, the loader
  stays where it is. It jumped 232 px to the left and 3 px down before. (#12570)
- **The summary comes into view after a tall card.** The first reply after a data card scrolls into
  view as it arrives while the focus is in the message box, so on a phone it no longer lands below the
  fold. (#12570)
