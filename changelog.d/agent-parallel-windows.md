### Changed

- **The agent chat's windows work in parallel; only their sandbox runs queue.**
  A paste, a chat turn, a data step (bindings, `.confirm()`, `.undo()`,
  `.to_long()`, the language, a library switch), the theme toggle and a file
  conversion in one browser window no longer answer `409 run_active` because
  another window of the same user renders a plot: every exclusion in the
  agents service is now per session (`Runtime.active`, `Runtime.pasting`,
  `Runtime.converting`), and within one session it stays one thing at a time.
  Plot runs and data snippets still share the run queue, at most three per user
  queued or running across windows (`AGENT_USER_MAX_RUNS`); a fourth ends its
  turn with the new stream error `run_limit`, which the page words as "you
  already have 3 plots or data runs in progress in other windows", instead of
  `capacity`. The per-user rate limits and daily budgets are unchanged (owner
  decision of 2026-10-21).
