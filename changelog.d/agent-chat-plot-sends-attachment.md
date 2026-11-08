### Changed

- **The plot button sends, reads and plots in one click.** With a file opened with `.open()`, a
  pasted table or a typed table in the message box, `.create_plot() →` (after a plot
  `plot the new data`) is active: it sends the data as Enter would, with the typed text as its note, and
  once the reading comes back clean the page confirms the data and starts the plot by itself.
  A reading that is not clean (a required role without a column, a warning on the data card or
  from the server's binding check, a question back from the assistant, a refusal, an error or a
  stop) halts at the data card, and the status line says what to look at. Typing or another
  click while the reading runs ends the chain, which never plots twice. Enter still only sends.
  Until now the button stayed greyed out with an attachment in the box, and only Enter read it.
  (#12833)
