### Fixed

- **`.env` is read only from the checkout root.** The API, the Postgres sync
  script and the workflow agent module called `load_dotenv()` without a path,
  which walks up the directory tree from the calling file. In a git worktree
  under `.claude/worktrees/` that walk reaches the main checkout's `.env` and
  loads the production database credentials into a test run or a local server
  that never asked for them. Each call now names its own checkout's `.env`; a
  missing file is still silently skipped, so Cloud Run and GitHub Actions, which
  set their variables directly, are unchanged. (#12105)
