### Added

- **`/debug` shows a feedback case's turn record.** The case detail gains a
  `# turns` block: one row per turn with the page's action or a message, how
  the turn ended, and as chips the guards that fired and the tool calls,
  identical neighbours folded (`get_dataset_profile ×2`). A failed render, a
  broken tool or a lost reply marks its row red; a refusal, a refused call
  such as `plot_as_confirmed`, a cap or a reply check that changed the reply
  marks it amber. Selecting a row opens the turn's whole record: every call
  with its verdict, outcome and code, every guard verdict in order, the
  `prep_ops`, and what the bounds left out. The transcript labels each user
  line with its turn number, so a row leads to its message. A case sent
  before the record says so instead. `GET /debug/agent/cases/{id}` carries
  the record as `turns`, every code closed again to the record's
  vocabularies, which a test pins to the agents service's. (#13044)
