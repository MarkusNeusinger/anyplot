### Fixed

- **A plot change asked for together with a data change reaches the plot.**
  One message could change the data and ask for a change of the plot ("drop
  these rows and use a log scale"). The data changed, the assistant wrote
  that the log scale was noted, and the plot of the new data came without
  it: a change of an existing plot was never kept, and the plot button
  brings no request. The chat now keeps such a change while the data or the
  bindings wait for the user's check, and "plot the new data" draws it on
  the latest plot together with the new data. A note for a first plot
  behaves as before. (#13061)
