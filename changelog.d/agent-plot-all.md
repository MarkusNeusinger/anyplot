### Added

- **`.plot_all()` in the admin agent chat: one table, a plot in every library at
  once.** In step 2 the page replays the confirmed upload and bindings in a
  session per enabled library, without the summary turn, and runs their plots
  through the normal run queue, at most `AGENT_USER_MAX_RUNS` at a time, which
  `GET /status` now reports as `user_max_runs`. The results show as a grid of
  cards with each library's status, image and `.stop()`.
