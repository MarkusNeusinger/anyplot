### Changed

- **Gemini second opinions run through Vertex AI, and Claude no longer runs
  agy.** Google's Antigravity FAQ and a staff reply of 2026-10-16 forbid
  running the Antigravity CLI from third-party coding agents under a consumer
  login, even read-only. `CLAUDE.md`, `.claude/guardrails.md` and the
  `gemini-task` skill now send first reviews and second opinions to Gemini 4
  Argon through Vertex AI in project `anyplot`, with read-only tools. Only the
  owner starts agy, for `gemini`-labelled tasks. (#12226)
