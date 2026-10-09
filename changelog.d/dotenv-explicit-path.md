### Fixed

- **`.env` is read only from the checkout root.** The API, the Alembic
  environment, the Postgres sync script, the workflow agent module and the e2e
  test fixtures called `load_dotenv()` without a path, which walks up the
  directory tree from the calling file. In a git worktree under
  `.claude/worktrees/` that walk reaches the main checkout's `.env` and loads the
  production database credentials into a test run, a local server or a
  migration that never asked for them. Each call now names its own checkout's
  `.env`; a missing file is still silently skipped, so Cloud Run and GitHub
  Actions, which set their variables directly, are unchanged. (#12105)
