### Added

- **One working line at the foot of the agent chat, with the plot's clock.** Every turn in flight
  says what it does now beside the site's loader, on both lanes: `drawing your plot · 0:42`, from
  the second try on with the try (`second try`, or `try 2 of 2` from the server's round cap),
  `waiting · you are 3rd` while the own turn waits in the run queue, the words of a turn without
  plot work, and `writing the reply` below the card. It replaces the thread's in-progress line,
  the progress timeline below the thread and the queue counter, so one position shows on screen.
  The status line counts the same clock beside `usually 1–3 min`, hidden from the plot button's
  description, and a shipped card keeps it as `ready in 1:12`. A phone reads `drawing · 0:42`.
  (#12950)
- **The service's mood on the chat window's tab.** `~/anyplot.ai/agent · ● quiet`, `● busy` or
  `● resting until 01:00` on the visitor's own clock, the same for every visitor and for an
  admin, from the one reader of `/status`, which reads again after each run, when the tab becomes
  visible again and every 60 s while it is visible. A `service_paused` refusal rests it at once.
  It replaces the pause note above the composer. On a phone the resting mood reads
  `● back at 01:00`. (#12950)
- **The progress grid and the admin meters in the admin menu.** The running turn's grid moved
  from below the thread into the admin menu, and on the admin lane the menu shows
  `now 2 runs · today 62 %`, read again as it opens, also during a run. The day budget's share is
  one function for the debug page and the chat, so the two never disagree. (#12950)

### Changed

- **Shorter message box placeholders on a phone.** A phone cuts a placeholder without an
  ellipsis, so below 600 px the box reads "ask or say what to plot" before the first plot and
  "ask for a change" after it; the wider screen keeps its longer words. (#12950)
