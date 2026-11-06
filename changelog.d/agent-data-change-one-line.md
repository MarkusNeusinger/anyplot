### Changed

- **A lost confirmation is announced once, and a refusal reads in plain words.** After a change to the data or the
  bindings the user had confirmed, or when the server no longer held the confirmation, the thread showed a notice
  ("# data changed · check it, then plot the new data", "# bindings changed · check them, then .create_plot()",
  "# check the data again, then .create_plot()") right above the composer's step line, which said the same; the
  step line is now the one line (the data card's own header stays). A refusal is labelled in plain words
  ("can't fetch data", "outside this chat", "chat paused", ...) instead of "refusal · needs_data", with the code
  behind the label's ⓘ; the admin fan-out panel keeps "refused · needs_data" with the same plain label under it.
  (#12586)
