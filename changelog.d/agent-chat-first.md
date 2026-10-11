### Changed

- **The agent chat is one column, and the data is its first turn.** The data card
  (paste, preview, bindings, the `# changed` block with `.undo()`, `.confirm()`) opens
  the thread, the assistant's summary follows it, and a correction in words updates the
  card in place. After `.confirm()` the card collapses into a header pinned at the top
  of the thread, `✓ data fits · N rows · M columns · version V`, whose `.show()` opens
  the full card again without leaving step 2; any binding change, undo, data request or
  new paste takes the page back to step 1 with the card open, and the header stays as
  `! confirm again`, so the card is one `.show()` away from anywhere in the thread. A
  table read from free text holds the page in step 1 until `.use()` or `.discard()`.
  Keyboard focus follows the steps without stealing it from the composer, and a second
  key press never stops the run the first one started. In step 2 the composer's
  filled `.create_plot()` starts the first plot as it is, or, with a note typed first
  ("log scale on y"), sends the note as the turn that makes it; once the library has a
  plot, the composer refines as before. The contracts, the session hook and the
  analytics events are unchanged; the root prompt gains two lines: a message in step 2
  before any plot is the first plot with that request (`plot_pipeline` with the
  `change_request`), and numbers about the data in a reply come from the latest tool
  result, never from an earlier turn. (#12137)
