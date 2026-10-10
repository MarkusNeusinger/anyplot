### Fixed

- **The root agent no longer reports a shipped plot as failed.** The chat UI
  added `version` to the plot result, but the tool-safety allowlist for the
  `plot_pipeline` result did not know the field, so every shipped plot reached
  the root as `invalid_result` and its closing reply told the user that the
  run had failed while the plot was already on screen. The allowlist is now
  derived from the `PlotResult` schema, and a test holds the two together.
