### Added

- **Example data on request in "Use with my data".** "Beispieldaten",
  "generiere Zufallszahlen mit Kategorien" or "monthly sales for 4 regions" in
  the data field no longer ends in "no table found": the dataset route answers
  `422 data_request` (fixed phrases in eight languages before any model, the
  free-text reader's new `asks_for_data` for the rest) and the page sends the
  text to the chat as the user's message. The assistant reads the plot's data
  roles and writes seeded Python that `run_data_code` runs in the sandbox, so
  no model writes a row; the data panel's change line says
  `generated example data`, and the same works when asked in the chat.
  (#12509)
