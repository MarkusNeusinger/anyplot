# The chat reads and rebuilds from the original table or an earlier version

- Date: 2026-11-06
- Proposed: both data tools read only the current version, so in persona tests the chat told users
  three times to press `.undo()` or paste again.
- Decided: the chat reads and rebuilds from the original table or an earlier version and says so,
  and a rebuild is stored as the next version on top. On 2026-11-07 he set that the session numbers
  every data version once.
- Where: #12600, #12616, `docs/concepts/agent-network.md`
