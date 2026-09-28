### Changed

- **A kept regeneration stores its re-score.** When the regen gate keeps the
  live implementation, the review's re-score of it (score, weaknesses,
  strengths, image description, checklist and review model) replaces the
  stored review through a metadata pull request that `impl-merge.yml` merges,
  so the next regeneration starts from current problems under the current
  model and rules. The review writes the re-score as `review_prev.json`, its
  checklist equal to the gate's `prev_checklist`; the new
  `automation/scripts/regen_writeback.py` checks it, writes the metadata and
  the `Quality: N/100` header number, and guards the merge (the score must be
  the kept PR's gate record's, only the review keys may change, and `main`
  must still hold the files the re-score judged). The code and the production
  images stay as they are; the gate record's new `writeback` key and
  `gate-report` count what happened on every keep.
