### Fixed

- **A review that fails after scoring is re-run instead of stranding the PR.**
  `impl-review.yml` retries every call of "Add quality score label" four times
  with backoff, and a run that dies after the score but before any verdict
  label now dispatches one fresh review on its own ref (sharing the existing
  `review-retry` budget), or labels the PR `ai-review-failed` for the watchdog.
  The watchdog's never-reviewed case also counts a lone `quality:N` as a
  marker. Before, an HTTP 502 on the label left PR #11984 without a verdict
  for about seven hours. (#12004)
- **impl-generate's auto-retry runs on the ref that dispatched it.** A branch
  smoke's failed generation used to retry on main (#11969–#11971); the retry
  now passes `--ref` with the run's own ref, which is `main` for every
  label-triggered run. (#12004)
- **Repair exhaustion no longer pushes to main.** After four failed repairs,
  `impl-review.yml` ran `git push origin main` to delete the pair's
  implementation, which the main ruleset refuses, so the step died after
  closing the PR and before labelling the issue. Only a forced regeneration
  reaches that point with an implementation on main, and that live
  implementation now stays: the issue gets `impl:{library}:done` back. A
  fresh pair is marked `impl:{library}:failed` as before. (#12004)
