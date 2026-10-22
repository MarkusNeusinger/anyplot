### Changed

- **Gemini second opinions run through Vertex AI, and Claude no longer runs
  agy.** Google's Antigravity FAQ and a staff reply of 2026-10-16 forbid
  running the Antigravity CLI from third-party coding agents under a consumer
  login, even read-only. The new `zweitmeinung` project skill calls Gemini
  through Vertex AI in project `anyplot` with read-only tools: Gemini 3.8 Flash
  on half-price Flex PayGo for first reviews of normal PRs, and Gemini 4 Argon
  for plans and second opinions. Its script inlines the diff and the changed
  files and reads several files per call, because every tool turn re-sends the
  whole conversation; unit tests pin its read-only confinement and tool loop.
  `CLAUDE.md` and `.claude/guardrails.md` describe the split and its measured
  costs. (#12226)
- **Gemini hands its work over as a draft PR.** In the `gemini-task` skill,
  Gemini pushes its `gemini/*` branch and opens a draft PR labelled `gemini`,
  so CI runs at once while Copilot waits; Claude reviews the draft and marks it
  ready. The owner may let Gemini run tests and builds unattended in his own
  agy session, and only he starts agy. (#12226)
