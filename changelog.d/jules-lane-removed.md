### Removed

- **Google Jules lane.** Google announced on 2026-10-29 that Jules takes no
  new sessions after 2026-11-11 and shuts down on 2026-12-31, so the lane
  leaves `CLAUDE.md`, `.github/copilot-instructions.md`, and the guardrails,
  together with the `jules-task` skill and the Jules MCP server in `.mcp.json`.
  In its three test rounds Jules paid off only for work a command can verify:
  three of nine page-split variants kept their page unchanged. The checks that
  proved it (a jsdom snapshot with the existing test's mocks, a browser
  comparison against the production API) move into the `gemini-task` skill,
  where behaviour-preserving refactors go. The CI conditions that keep Jules
  and Dependabot PRs away from secrets stay until Jules stops taking sessions.
  (#12453)
