### Fixed

- **The review job checks a regeneration's chat readiness itself.** impl-review scanned no
  code for the agent chat's validator: it read the record the generate or repair runner had
  staged, where the generating model had a shell, so a forged record could hide a new refusal
  or claim a file the chat refused was now usable. "Readiness check" now scans the PR head and
  the file on `main` itself, before any model session of the job, with the validator and its
  pinned pydantic from the workflow's own ref. A scan that starts and doesn't finish keeps the
  live implementation; when the scan can't run at all, the staged record still counts, but
  only to keep. (#15197)
