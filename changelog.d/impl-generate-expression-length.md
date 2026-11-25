### Fixed

- **Generation runs start again.** After the follow-up regenerations of
  #14244, GitHub refused the generation workflow: its failure step had grown
  past the 21,000-character limit GitHub sets for a value that holds an
  expression, so no generation could be dispatched and the nightly
  regeneration of 2026-11-25 ran none. The step now reads the run's link and
  the repository from environment variables, so it holds no expression, and a
  test keeps every workflow value with an expression well below the limit.
  (#14254)
