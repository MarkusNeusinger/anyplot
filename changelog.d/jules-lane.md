### Added

- **Google Jules takes short implementation tasks.** The new `jules-task`
  skill hands credential-free tasks that fit a roughly 30-minute cloud run to
  Jules through Google's official MCP server (`.mcp.json`, key read from
  `.env`). It covers single tasks against `main`, parallel sub-tasks of a
  `feature/*` branch, and best-of-N comparisons when the approach is open, and
  bundles a session watcher that flags empty PRs. The Ultra plan allows 300
  tasks a day, each counted once, so this work no longer costs Claude tokens.

### Changed

- **Delegation lanes after the first Jules test.** The delegation rule in
  `CLAUDE.md` and `.claude/guardrails.md` now gives Sonnet a narrow lane for
  bounded work a command verifies, sends ~30-minute implementation to Jules
  and larger steps to `/gemini-task`, and runs Fable plus Gemini 4 Argon only
  when the owner asks for a second opinion. Claude merges Jules's sub-PRs into
  a `feature/*` branch it leads; every merge into `main` stays with the owner.
  The guardrails record the Gemini 3 Pro against Flash comparison that made
  Flash the Jules model.
- **Gemini Flash checks every PR before it opens.** `/open-pr` now runs
  `/zweitmeinung` with Gemini 3.8 Flash on the branch diff before the PR
  opens, so Copilot's single round ideally finds nothing.
