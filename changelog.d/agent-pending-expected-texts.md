### Fixed

- **A kept plot note keeps its requested texts.** When a first plot stops
  before the confirmation, the texts and number formats the user asked to see
  (`expected_texts`) are now kept with the note, so the next bare
  `.create_plot()` checks the render for the same title or format; a run that
  brings its own request or texts checks only its own, so a withdrawn title is
  never reported missing. The note follows one lifecycle: kept until a plot
  ships, kept through a binding change that only fills roles that were still
  open, dropped by any other change to the bindings, the data or the library.
  (#12186)
