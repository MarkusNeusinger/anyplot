### Added

- **Gemini takes coding tasks through `gemini`-labelled issues.** Claude writes
  the task as an issue, the owner works it with Gemini 4 Argon in his
  interactive agy session in a separate clone with pushing disabled, and Claude
  reviews the branch and ships it as a PR (`/gemini-task`). Gemini's quota does
  the implementation, while credentials and every outside write stay with
  Claude.

### Changed

- **Delegation runs in lanes.** The delegation rule in `CLAUDE.md` and
  `.claude/guardrails.md` now assigns each lane:
  - Opus for anything that changes state,
  - Haiku only for reading and polling,
  - Fable for high-risk reviews,
  - Gemini for credential-free reading, first reviews and implementation.

  Sonnet no longer has a lane in interactive sessions. The guardrails also
  record why headless Gemini implementation was dropped: agy's login is a
  project-owner token, Google front ends route by `Host` header, and proxying
  the token breaks the Antigravity terms.
