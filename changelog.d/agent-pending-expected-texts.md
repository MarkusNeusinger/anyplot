### Fixed

- **A kept plot note keeps its requested texts.** When a first plot stops
  before the confirmation, the texts and number formats the user asked to see
  (`expected_texts`) are now kept with the note, so the next `.create_plot()`
  checks the render for the same title or format. They follow the note's
  lifecycle: kept until a plot ships, dropped by any change to the bindings,
  the data or the library.
