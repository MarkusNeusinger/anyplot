# About 30 minutes without a commit or a message counts as a suspected stall

- Date: 2026-10-31
- Proposed: on 2026-10-30 a build agent stopped at midday while waiting for its own tests. A
  context summary called it "still working", and in the evening he was the one who asked whether
  anything was still running.
- Decided: recorded on 2026-10-31, in a list of rules he approved after that session. A delegate
  with no new commit and no message for about 30 minutes is a suspected stall: the main session
  checks its real state and reports it, also after every compaction.
- Where: #12493, `.claude/guardrails.md` ("Long-running work reports progress proactively")
