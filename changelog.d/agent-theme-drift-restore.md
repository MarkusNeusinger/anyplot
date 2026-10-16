### Fixed

- **A repair that only changes the protected theme statements still renders.** When an adapter
  answer fails its check only because it changed the `THEME` assignment, a theme token or the final
  savefig, and the round's check retry fails the same way, the pipeline puts the original
  statements back (`edits.restore_protected`) and checks, renders and reviews the rest of the
  repair, instead of ending the round and shipping the earlier render. A theme name bound a second
  time is never restored. `pipeline_check` logs the outcome `drift_restored`, and the
  `pipeline_run` telemetry line and the `pipeline_runs` view gain a `drift_restored` flag. (#12209)
