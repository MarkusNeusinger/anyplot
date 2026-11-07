### Changed

- **The agent chat opens with what the plot needs.** The thread's first item
  reads "You came from **Basic Scatter Plot**. It needs", then the spec's
  roles as chips in the words of someone with a table, not a dtype
  (`x · numbers`, `numbers or dates`, `y · numbers, one or more` for a family,
  `series · categories, optional`), beside the catalogue plot's thumbnail in
  the library in use, and ends with "drop a file or paste a table below". The
  thumbnail, the columns ⓘ (now after the chips) and the how-to ⓘ moved there
  from the header row, which keeps the title, the library and the language.
  The item repeats no control, since `.example_data()` and `.open()` stand in
  the line above the message box; it is a message in the thread, so it stays
  first and scrolls up with the talk once data arrives. On a phone it is
  compact: a smaller thumbnail beside the first line, the chips below it.
  (#12596)
