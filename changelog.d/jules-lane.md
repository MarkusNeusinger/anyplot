### Added

- **Google Jules takes short implementation tasks.** The new `jules-task`
  skill hands credential-free tasks that fit a roughly 30-minute cloud run to
  Jules through Google's official MCP server (`.mcp.json`, key read from
  `.env`). It covers single tasks against `main`, parallel sub-tasks of a
  `feature/*` branch, and best-of-N comparisons when the approach is open, and
  bundles a session watcher that flags empty PRs. The Ultra plan allows 300
  tasks a day, each counted once, so this work no longer costs Claude tokens.
  (#12429)

### Changed

- **Delegation lanes after the first Jules test.** The delegation rule in
  `CLAUDE.md` and `.claude/guardrails.md` now gives Sonnet a narrow lane for
  bounded work a command verifies, sends ~30-minute implementation to Jules
  and larger steps to `/gemini-task`, and runs Fable plus Gemini 4 Argon only
  when the owner asks for a second opinion. Claude merges Jules's sub-PRs into
  a `feature/*` branch it leads; every merge into `main` stays with the owner.
  The guardrails record the Gemini 3 Pro against Flash comparison that made
  Flash the Jules model. (#12429)
- **Gemini Flash checks every code PR before it opens.** `/open-pr` now runs
  `/zweitmeinung` with Gemini 3.8 Flash on the branch diff before a code PR
  opens, so Copilot's single round ideally finds nothing. Diffs made only of
  docs, instruction files, changelog fragments, or `plots/`, and diffs under
  about 20 lines, skip it. (#12429)
- **Lint and tests run on pull requests into `feature/**`.** `ci-lint` and
  `ci-tests` now also run for PRs into a feature branch, so every Jules
  sub-PR is checked before Claude merges it. Image builds, migrations,
  CodeQL, and the changelog check stay on PRs into `main`. (#12429)

### Security

- **Jules and Dependabot PRs run CI without secrets or an OIDC token.**
  `ci-tests.yml` splits into `Run Tests` (unit and integration, no
  `id-token` permission, every author) and `Run E2E Tests`, the only job that
  logs in to GCP, starts the Cloud SQL proxy, and holds the database password;
  it runs after `Run Tests` and skips PRs by `dependabot[bot]` and
  `google-labs-jules[bot]`. `ci-image.yml`'s `renderer-image` skips Jules PRs,
  and Jules opens PRs only into `feature/*`. Before, a Jules PR ran its tests
  with production database access the moment it opened. Every condition uses
  the PR author, because `github.actor` on Jules branches is often the
  repository owner and a re-run can change it. (#12429)
