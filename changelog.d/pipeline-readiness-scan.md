### Added

- **The pipeline records when a new version stops working in the agent
  chat.** impl-generate and impl-repair scan a Python implementation and its
  predecessor on `main` with the chat's validator
  (`automation/scripts/readiness_scan.py`) and record the refusals only the
  new file has. Record-only: one log line, a job-summary line, and
  `adapt/readiness.json` in staging; nothing reads it yet. On the six
  regenerations of 2026-11-11 it finds two regressions, one of which turned
  a file the chat accepted into one it refuses.
