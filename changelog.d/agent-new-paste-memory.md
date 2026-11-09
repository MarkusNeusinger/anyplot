### Changed

- **A plot wish pasted with new data reaches the plot of that data.** The
  assistant's `keep_plot_request` refused a note once the library had a plot,
  so a title typed with a second paste never reached its plot. A plot of data
  that a later paste replaced is no plot of the current data now: the note is
  kept for the first plot of the new data, also when the assistant sends it as
  a change of the old plot, and the session block tells the assistant so. Each
  shipped version records the data version it drew. (#12832)
- **New data drops what a library switch carried.** A paste, a change of the
  data, `.to_long()` and an undo drop the switch's carry (the theme, the texts
  and the requests of a plot of the data before), as they already drop a kept
  first-plot note, and the page ends its offer with them. A switch or the admin
  fan-out's copy after the data changed takes only the theme you asked for on
  the plot of the earlier data, never its texts or requests, besides the
  remembered decisions, so the public and the admin lane treat a new paste
  alike. (#12832)
- **The remembered decisions show where new data meets them.** When a paste
  lacks a column the data before it was bound to, the paste answer says
  `columns_changed`, and the new `# data` line holds the decisions until the
  next plot: `3 earlier decisions ▾ · .forget_all()`. One click forgets them
  all; ignored, they stay, since only the user clears the memory. (#12832)
