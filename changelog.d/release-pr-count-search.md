### Fixed

- **The release procedure counts merged pull requests with the search API's
  total.** Step 4 of `agentic/commands/release.md` counted them with
  `gh pr list --limit 5000`, which stops at 1,000 results whatever the limit,
  so the count read exactly 1,000 at the v4.2.0 cut while 1,038 had merged.
  It now reads `total_count` of a GitHub issue search.
