### Added

- **A feedback case explains itself.** Each pipeline round now carries the ids
  of the gates its renders failed (`R1`, `G8`) and the closed class of a crash
  (`key`, `timeout`), and every session bundle names how many versions the
  session held and how its latest plot run ended. A chat case, which holds no
  version, now tells a plot the page missed from a run that failed, and the
  `/debug` case view shows a line per round and the session's line. All of it
  is closed codes and counts, never a message or a cell of the data. (#12552)

### Fixed

- **Pictograms, waffles, dot matrices and parliaments no longer read as made-up
  data.** The render gate that counts more point marks than rows (G8) now skips
  the plot types that draw one mark per unit of a count, so a pictogram of 11
  rows that draws 77 icons is no longer sent to a repair to "draw marks only
  from df". Every other plot keeps the check, and the ceiling on plotted points
  still holds for all. (#12552)
- **The reply after a shipped plot no longer asks to confirm the data.** A code
  check drops every sentence that names `.confirm()` from the assistant's reply
  in a turn whose plot shipped, because a shipped plot was drawn from confirmed
  data. The rest of the reply stays word for word, and the check costs no model
  call. (#12552)
