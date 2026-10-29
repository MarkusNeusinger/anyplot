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
- **Gemini Flash checks every code PR before it opens.** `/open-pr` now runs
  `/zweitmeinung` with Gemini 3.8 Flash on the branch diff before a code PR
  opens, so Copilot's single round ideally finds nothing. Diffs made only of
  docs, instruction files, changelog fragments, or `plots/`, and diffs under
  about 20 lines, skip it.
- **Lint and tests run on pull requests into `feature/**`.** `ci-lint` and
  `ci-tests` now also run for PRs into a feature branch, so every Jules
  sub-PR is checked before Claude merges it. Image builds, migrations,
  CodeQL, and the changelog check stay on PRs into `main`.

### Security

- **Jules PRs run CI without secrets.** A PR opened by
  `google-labs-jules[bot]` now takes the Dependabot path in `ci-tests.yml`
  (no GCP login, no Cloud SQL proxy, no database password, no e2e, no Codecov
  token) and builds without the Artifact Registry login in `ci-image.yml`.
  Before, a Jules PR ran its tests with production database access the moment
  it opened, before anyone had read the code. The check uses the PR author,
  because `github.actor` on Jules branches is often the repository owner.
