### Changed

- **One number per data version, the same on the card and for the assistant.**
  The agents service numbers every data version once per session, across
  pastes, picks, changes, `.to_long()`, copies and computed tables, and never
  gives a number twice: a paste, a change, an undo and a change are v1, v2, v1
  and v3, and a second paste is v4. The data card shows that number, and after
  an undo it carries the number of the version it went back to
  (`data v1 · back to v1`). Until now the page counted versions itself while
  the server's number started over with every paste, so since `from_version` a
  user who asked for "v2" could get a different table from the one the card
  called v2. Every dataset answer and `done.dataset` now carries `can_undo`,
  which the page reads for `.undo()` instead of guessing from the number, and
  `original_version`, from which the `agent_data_undo` bucket still counts the
  paste as 1.
