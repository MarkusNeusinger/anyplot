### Added

- **The assistant answers a request for another plot type.** Asked for a violin plot or for the plots that would
  suit the data, it says in one or two sentences that switching the plot type in the chat is planned but not
  possible yet, may name a kind of plot that fits the data, and points to the catalogue at anyplot.ai/plots, where
  each plot's page leads to its own chat and the data is pasted again. It never says the catalogue has a
  particular type, since it does not know the catalogue. The scope judge reads such requests as in scope, with four
  new cases in the scope eval and four in the prep eval, in English and German.

### Changed

- **One click from checked data to the plot.** `.confirm()` is gone: from the moment data is stored,
  `.create_plot()` stands at the composer's right end as the filled button, confirms the data and its bindings as
  the card shows them and starts the plot in the same click, with the typed text as the plot's request when the
  box holds any. A refused confirmation starts nothing and shows under the composer. The line above the message
  box says what the click still waits for: a table read from text to decide on, or a column for a required role.
  After a change to confirmed data `.create_plot()` is filled again, also when the library already has a plot.
  `.send()` shows only while the box holds text, and Enter never confirms. The admin's `.plot_all()` and the plot
  after a library switch confirm the same way. At phone width the buttons wrap below the box and stay at its right
  end. The assistant's prompt and the session block send the user to `.create_plot()` instead of `.confirm()`.
- **A pasted formula or code goes to the chat by itself.** The data box no longer offers `.send()` when the server
  answers `422 formula` or `422 code`: the page sends the text to the chat as your message at once, as it already
  did for a request for data, and empties the box. Code over the chat's 2,000 characters stays in the box with a
  line that asks to shorten it. `agent_data_parsed` reports such pastes as `formula` or `code` instead of `error`.
- **The site's loader marks the chat's waits.** The three-dot `LoaderSpinner` of the plots gallery, in a new inline
  size, replaces the pulsing ellipsis while a session opens, in the thread's in-progress line, beside a plot run's
  progress and over the data box while a file is read or the data is parsed, one moving indicator per wait: the
  lines that only say what waits lost their ellipsis, and a question or a summary waiting in the queue shows the
  in-progress line and the queue counter without the progress grid. `.example_data()` steps aside while its turn
  runs, keeping its room, so "making example data" shows once, in the thread. The loader, in the gallery too, drops
  the ochre: a resting pair in the theme's warm gray of muted text and a runner that turns green while it crosses
  them. Its dots stand still under reduced motion, the runner green, and each size has keyframes of its own, so two
  sizes on one page no longer share one animation.
