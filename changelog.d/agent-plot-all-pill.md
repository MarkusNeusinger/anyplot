### Changed

- **`.plot_all()` in the admin agent chat is chosen in the library selector.** An
  `all` pill after the header's library pills turns the composer's create action
  into `.plot_all()`, which replays the confirmed table in every library at
  once; the separate row under the composer is gone. While `all` is pressed the
  page's own session stays the data session; in step 2 the message box waits,
  since the fan-out takes no typed text, while the chat about the data in step 1
  goes on. Any library pill turns `all` off again. Data the assistant changed or
  computed keeps `.plot_all()` disabled, with a line that says why.
