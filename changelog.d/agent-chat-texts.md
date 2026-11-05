### Changed

- **The assistant's replies are shorter and never walk through the page.** In the agent chat, a reply
  is one or two short sentences with the counts that matter, four at most with a notice it must
  carry. It no longer tells the user to check the data panel or press `.create_plot()`, which the line
  above the message box already says, nor what the notes do not hold. It no longer counts the plot's
  labels the server checked, and a note the server made from a column with one value in every row
  reads `Currency: USD (the same in every row)` in the data card, which the reply states as a fact of
  the data rather than as the user's note.
- **The result card's notes read in plain words.** One line per issue, such as `some labels overlap`,
  replaces the review's lines with their rubric ids, pixel counts and code; the lines in full stay
  behind the notes' ⓘ.
- **A repair round reads as the normal course.** In the progress grid, a review that found things to
  fix keeps a dot and says `3 things to fix` in a neutral ink, where it showed a red `✗ review: 3
  findings`; a repair round says `fixing text size, layout`, and the shipped round's `~ 1 note left`
  points at the card's notes. A failed render or code check keeps its red ✗.
- **The thread names the buttons the user pressed.** A plot turn shows as `.create_plot()`,
  `.start_over()` or `plot in plotly with your 3 decisions`, not as the action `.carry_plot()` the
  page sends, and the summary after a paste, which no button sends, shows no line. Inline code in a
  reply shows as code, without its backticks.
- **The line above the message box says how to stop a running plot.** While a plot runs it reads
  `# plotting… .stop() to cancel` in place of the step's line, which still invited the click that
  started the run.
