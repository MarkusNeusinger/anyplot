### Changed

- **Weekly regen review opens at most 15 renders.** `collect_week.py` now ranks suspicious regenerations
  (merges carried only by `P` or `new` defects, then big re-score drops on keeps, then gate oddities,
  then scores of 90 or more), fills the sample at random up to 15, and lists the suspicious PRs over the
  cap as "not opened". The skill runs only when the owner asks; there is no schedule (#12056).
