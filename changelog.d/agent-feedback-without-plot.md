### Added

- **A chat that made no plot can be reported too.** Below the composer, a session
  without a plot version offers `.feedback()` on the chat itself, the same four
  reactions, text and `# include data.csv`. It is stored as a feedback case with
  `result_version` 0: the conversation, the profile, the bindings and, when ticked,
  the session's current data, but no image and no `plot.py` (`422 no_data` when the
  data is asked for before there is any). The triage labels it `chat, no plot`,
  shows no renders and refuses its promotion (`422 no_plot`), and `import_case`
  refuses it. No migration: `result_version` had no constraint (#12155).
