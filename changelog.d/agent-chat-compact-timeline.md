### Changed

- **A repair reads as one more round, not as every step again.** The chat's progress
  timeline folds a finished round into one entry (`first try done`) and lists only
  the current round's steps, instead of repeating each step with `· attempt 2`; the
  result card says `1 repair` instead of `2 attempts`.
