# A user may paste 100 times a day and convert 30 files, checked before any model runs

- Date: 2026-10-14
- Proposed: every paste reaches the parser and the model judges, and every dropped file the sandbox.
- Decided: at most 10 pastes a minute and 100 a day per user, across sessions, checked before any
  parser or model; only a paste that reaches a check counts. On 2026-10-15 he set file conversions
  at 5 a minute and 30 a day.
- Where: #12180, #12194, `docs/concepts/agent-network.md`
