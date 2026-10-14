### Fixed

- **The plot result reports the changes the shipped code carries, not the
  proofread's notes.** `PlotResult.changes` came from the plan of the last
  adapter call, which in the live flow is the self-review; when it changed
  nothing its "already present" notes replaced the real changes, and the
  assistant told the user the change might not have run. The changes are now
  the notes of every adapter call up to the shipped render whose plan changed
  the code, so a shipped earlier round reports its own (`pipeline.note_changes`).
- **An earlier explicit request is no longer undone by the review loop.** A
  title the user had chosen two turns earlier was rewritten when a later change
  ran, because neither the adapter nor the reviewer knew it was the user's
  choice and the rubric judged it. Each plot version now keeps the change
  requests it carries out, a change hands them to every adapter call and to the
  reviewer as fenced standing requests (the most recent 8 within 2,400
  characters), and the adapter and reviewer prompts keep them: never a defect,
  changed only when the current request asks for it.
