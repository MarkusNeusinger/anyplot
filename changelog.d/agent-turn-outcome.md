### Added

- **The chat stream says what a turn changed, which decisions a plot kept, and the round cap.** A turn that ends
  well closes with `done.turn` (`answer`, `data`, `plot`, `switch`, `language`, `kept` or `memory`), which the
  agents service derives from a new per-turn record of the assistant's tool calls (closed tool names, the guards'
  verdicts and a closed outcome per call, never an argument) instead of from the reply. A stored version's `plot`
  event carries `memory: {kept, added}`, the plot memory entry ids it stands on, and every pipeline step's `status`
  carries `max_attempts`. The page can then tell a question from a turn that only kept a wish for the first plot,
  label a version `kept 3`, and say "try 2 of 3" from the server's numbers; an older page ignores all three.
  (#12607)
