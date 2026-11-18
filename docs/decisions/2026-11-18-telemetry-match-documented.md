# A way to match a telemetry line to its request is documented, not hidden

- Date: 2026-11-18
- Proposed: a privacy review found that a telemetry line's token counts equal the sums of its
  request's log lines, so the two can be matched for the 30 days those lines are kept. The options
  were to break the match in code or to document it.
- Decided: document it. The reason is the one the agents gave him with the options: the match by
  time gives the same readers the same link for the same 30 days, so breaking this one would change
  little. The privacy page says in one sentence that both exist.
- Where: #13185
