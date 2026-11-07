### Changed

- **The agent chat's composer is the message box and the plot button.** The
  box with a brand-green border and a `❯` and the plot button share one row,
  on a phone too; one quiet line right above them holds `.example_data()` and
  `.open()` as links, `# no data at hand? .example_data() · .open() a file`,
  highlighted in green until the first data arrives, then muted, `# other
  data? .open() · .example_data()`. Nothing comes, goes or moves: a state
  changes how the line reads, fills the plot button once there is data, and
  makes a control inert with `aria-disabled`, so a focused one keeps the focus
  and a second key press does nothing. Targets are 44 px. Before data the box
  reads "paste a table or drop a file". (#12594)
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
