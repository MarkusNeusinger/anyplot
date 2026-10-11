### Changed

- **"Use with my data" runs in two steps: the data first, then the plot.** The data
  panel ends step 1 with `.confirm()`: you check the preview and the bindings, confirm
  that they fit, and only then does `.create_plot()` appear. The agents service enforces
  it (`POST .../dataset/confirm`; a plot on unconfirmed data is `not_ready` with
  `data_unconfirmed`), a new paste, a transcription's `.use()` or a binding change drops
  the confirmation, and a library switch keeps it. A step header `1 data · 2 plot` shows
  where you are. The design section "Two steps: data first, then the plot" in the
  agent-network concept doc records the owner's rule and the planned data operations.
