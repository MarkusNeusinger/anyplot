### Changed

- **A regeneration that the agent chat would newly refuse no longer replaces
  the live implementation.** The regen gate keeps the live version with the
  code `readiness_regression` when the chat's validator refuses the new file
  for something it did not refuse the predecessor for. In the first 24
  scanned regenerations three were such regressions, and two of them merged,
  so the chat now refuses two pairs it could adapt before. `impl-review.yml`
  gains the step "Readiness check"
  (`automation/scripts/readiness_record.py`): it reads the staged record of
  the readiness scan only when the record names the hash of the
  implementation at the PR head and of the one on `main`, and it recomputes
  the regression from the record's refusal keys. A missing, stale, or
  malformed record never keeps anything, and outside the regen gate (first
  generations, forced regenerations, repairs) the status is a record only. The
  scan's record now carries the two hashes (record version 2). The keep is a
  returning one: the pair comes back after the attempt window, not behind the
  whole catalogue. (#13113)
