# Usage records hold no user id, no hash of one, and no key that stays stable across sessions

- Date: 2026-10-30
- Proposed: the chat was about to open to anonymous visitors, and its telemetry and limits had to
  count per user.
- Decided: his rule: no user id, no hash of one, no key that stays stable across sessions. Each
  telemetry field is a closed set or a bounded integer, so nothing that names a user fits into it,
  and a test checks that the run's user id appears in no line.
- Where: #12507, `docs/reference/agent-telemetry.md`
