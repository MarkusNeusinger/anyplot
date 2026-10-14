### Fixed

- **Agent replies describe the rendered plot, not the plan.** The render probe now
  reports the drawn texts by role, and the plot result hands them to the root as
  `shows` with the review's verdict. The root names titles, labels and number
  formats only as the plot draws them. Before, its closing reply came from the
  adapter's notes, written before the render, so it claimed "6,5 Mio." on an axis
  that drew "6.0 M".
- **Requested texts and number formats are checked in code.** The root lists the
  texts the user wrote out (`expected_texts`), and the pipeline checks the drawn
  texts for each. A miss gets a repair round (`AGENT_EXPECT_CHECK=repair`), and a
  miss that no round fixes stays as a residual line, so the reply says so.
- **Data summaries name the real bindings.** `get_dataset_profile` returns the
  bindings in force, so the summary no longer describes the columns the profile
  suggests.
- **Titles know where the data comes from.** The adapter and the reviewer get a
  fenced dataset context: the screened notes pasted with the data and the source
  of a computed table (formulas, or the names in the user's code, such as
  `lorenz`). A Lorenz attractor is no longer titled "Trajektorie im Raum".
