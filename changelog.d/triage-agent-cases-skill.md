### Added

- **A project skill triages the agent chat's feedback cases in rounds.**
  `triage-agent-cases` lists the open cases read-only, copies their files to a
  private directory outside every checkout, and classifies each one as fixed
  (with the PR), in progress (with a failure-class tag and a general fix) or
  won't solve, in a private report. After the owner's OK for the round,
  `apply_triage.py` writes the statuses and tags in one transaction, after a
  snapshot of the rows, and refuses a row someone changed since the round read
  it. The cases hold users' data, so nothing of them reaches the repository.

### Changed

- **The triage rules of a case live in `core`.** `core.agent_cases.triage_updates`
  holds what `PATCH /debug/agent/cases/{id}` checks (tags, the promotion's
  plot, data and expected outcome), and the route and the skill's script both
  call it, so the two never drift apart. The route answers as before.
