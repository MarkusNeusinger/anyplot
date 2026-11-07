### Changed

- **The agent chat's composer is one row in four fixed places.** The message
  box with a brand-green border and a `❯`, `.open()`, `.example_data()` and the
  plot button stand in their places from the first moment; nothing comes, goes
  or moves. A state only moves the filled style, from `.example_data()` before
  there is data to the plot button after, and makes a button inert with
  `aria-disabled`, so a focused button keeps the focus and a second key press
  does nothing. The buttons share one size with 44 px targets. (#12594)
- **The plot button keeps its place and changes its name.** It stands quiet
  and inert before data, reads `.create_plot() →` with data, `.update_plot() →`
  once the library has a plot (it sends the box's text and waits while the box
  is empty), `plot the new data` after a change to confirmed data or a new
  paste, and `.plot_all()` with the admin fan-out on. After a library switch it
  keeps its name, and the status line names the decisions its plot keeps, in
  place of the "plot in seaborn with your 3 decisions" button. (#12594)
- **Enter sends, and `.send()` is gone.** On a touch screen, whose keyboard
  labels Enter "return", a small `↵` inside the message box sends too.
  (#12594)
- **`.stop()`, `.start_over()` and `.feedback()` stand at the end of the
  status line.** `.stop()` is a button of its own that Tab reaches, and hands
  its focus to the message box when the run ends; `.start_over()` waits there
  once the library has a plot, and `.feedback()` before the first plot opens
  the chat's feedback form above the line. While a plot runs the line reads
  `drawing your plot · usually 1–3 min`, and the admin fan-out's locked line
  moved into it from above the box. (#12594)
- **A reply never sends the user to the plot button.** `root.md` told the
  assistant in four places to say "press `.create_plot()`" while its reply
  rules forbade it; the instructions now leave the button to the status line,
  and ShippedReply drops a sentence that names `.create_plot()`,
  `.update_plot()` or `.plot_all()` in any turn, logged as `plot_button`,
  unless the user's own message asked about the button. Its sentence split no
  longer ends a sentence after an abbreviation such as "e.g." or "z. B.".
  (#12594)
