### Fixed

- **A result card's image actions stay off the plot on a phone.** Below 600 px
  the copy, download and open icons move from the image's top right corner,
  where the plot's title stands, into the card's header row.
- **The site's feedback button no longer covers the agent chat.** The chat has
  a feedback row on every result and one for a session without a plot. On a
  phone the site's button covered `.send()`, `.open()` and the replies' right
  edge, so the agent chat no longer shows it.
- **One plot button after a library switch with nothing to carry.** An offer
  without decisions showed `.create_plot()` and "plot in seaborn", which did the
  same. Now `.create_plot()` stands alone and still takes the switch's carry
  along. With decisions, the quiet button beside the offer reads `.start_over()`.
- **Popovers no longer shift the page.** A popover's scroll lock never stopped
  the page from scrolling, because the page clips its horizontal overflow at
  the root. It only padded the body, so the masthead and the right-aligned
  controls jumped 15 px as the library or language menu opened.
- **A file chosen with `.open()` hands the focus to the message box.** Enter
  then sends the file instead of opening the chooser again.
- **The result card takes the progress grid's place.** A run's card used to
  land above the grid while the reply was still being written, pushing the grid
  and the composer down until the turn ended. Now the card replaces the grid,
  and anything the run sends into the thread before its card waits for it. The
  agent BFF mock gains `MOCK_REPLY_MS`, the time the reply takes after the plot.
