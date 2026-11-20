# A replaced table leaves what the assistant sees, and the discussion stays

- Date: 2026-11-20
- Proposed: after a paste that replaced data, the assistant answered the note sent with it from the
  first table, three times out of three on production, although the turn named the new table. Three
  options: take the old table's facts out of what the assistant sees on that turn; make it read the
  new table before it answers; or let the reply check count only the table in force as a source of
  figures.
- Decided: the first, on his condition that the assistant keeps the general content of the
  discussion. His reason: otherwise it looks strange to the visitor who wanted to do something, found
  that it did not fit, adjusted the data and wants to try again, and the model has forgotten
  everything said before.
- Where: `docs/concepts/agent-network.md`
