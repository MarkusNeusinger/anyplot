### Changed

- **The agent chat's composer holds each step's one call to action.** In step 1, `.confirm()` now sits at the
  composer's right end as the filled button, after `.send()`, instead of at the data card's foot, and the line above
  the message box says what it still waits for: a table read from text to decide on, or a column for a required
  role. `.create_plot()`, `.start_over()`, the plot after a library switch and the admin's `.plot_all()` appear only
  in step 2, so the notice that said "confirm the data first" after a click on an early `.create_plot()` is gone.
  The assistant's prompt places `.confirm()` beside the message box.
- **A pasted formula or code goes to the chat by itself.** The data box no longer offers `.send()` when the server
  answers `422 formula` or `422 code`: the page sends the text to the chat as your message at once, as it already
  did for a request for data, and empties the box. Code over the chat's 2,000 characters stays in the box with a
  line that asks to shorten it. `agent_data_parsed` reports such pastes as `formula` or `code` instead of `error`.
- **The site's loader marks the chat's waits.** The three-dot `LoaderSpinner` of the plots gallery, in a new inline
  size, replaces the pulsing ellipsis while a session opens, in the thread's in-progress line, beside a plot run's
  progress and over the data box while a file is read or the data is parsed. `.example_data()` steps aside while
  its turn runs, so "making example data" shows once, in the thread. The loader's dots stand still under reduced
  motion, and each size has keyframes of its own, so two sizes on one page no longer share one animation.
