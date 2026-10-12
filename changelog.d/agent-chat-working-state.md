### Changed

- **The agent chat shows when it works, and why the controls wait.** After
  `.parse()` the card says `# parsing your data …` under the button, and every
  turn without pipeline steps (the summary, a question, a data request) puts an
  in-progress line in the assistant's slot of the thread, `summarizing your
  data …` or `working on your message …`, until the reply or the first pipeline
  step replaces it; the progress timeline shows only for a plot run, a queue
  position or pipeline steps, so the two never say the same thing. While
  anything is in flight the bindings block says `# bindings and .confirm() wait
  while the assistant works …` instead of leaving the dropdowns silently
  disabled. The lock itself stays, because the server runs one thing per
  session.
- **`.create_plot()` is always in the composer once there is data.** Before the
  confirmation it is the quiet button next to `.send()`, and a click calls
  nothing: a notice under the composer says `# confirm the data first ·
  .confirm() sits at the foot of the data card`, and its `.show()` scrolls to
  the button and focuses it (to `.use()` while a table read from text waits).
  Someone who scrolled to the foot no longer meets a composer that hides the
  step. The server's `data_unconfirmed` stays the backstop.
- **A lost confirmation is named where it happens.** When a binding change, a
  data request, an undo or a new paste drops a confirmation the user had given,
  the thread gets a warning notice (`# bindings changed · confirm the data
  again`), the card's step line repeats it next to `.confirm()`, and the pinned
  `! confirm again` header reads as a warning, the phrase in bold on a
  warning-tinted surface, rather than as a neutral line. The first binding
  setup after a paste, where nothing was confirmed yet, says nothing.
