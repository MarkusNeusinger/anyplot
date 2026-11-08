### Changed

- **"plot the new data" keeps what you tuned when it can.** The button has an
  action of its own now (`plot_new_data`). When the data comes from the paste
  the library's latest plot drew and the same columns stand in the same roles,
  the run changes that plot for the new data, with one request the server
  writes, so a title, colours or limits the remembered decisions never held
  stay. A new paste, a binding change or a reshape still starts from the
  catalogue plot with the remembered decisions, and now keeps the theme you
  asked for. The plot's `new_data` says which, the card's label names it
  (`new data on v3`), and `.start_over()` stands beside the button whenever
  the library has a plot. The usage telemetry counts the base per run.
  (#12834)
