### Changed

- **The PR watchers end on their own.** `watch-deploys.sh` exits 0 with
  `no deploy for <sha>` once 6 polls (about 3 minutes) have found no build
  for a merge whose paths trigger nothing, instead of waiting 30 minutes, and
  exits 2 at once when `gcloud builds list` fails, so a lapsed login never
  reads as "no deploy". `watch-checks.sh` waits 90 polls, about 45 minutes,
  because a PR that builds the renderer image takes 30 to 40, and its
  `TIMEOUT` line names the checks still pending.
- **The agent rules and skills carry what the 2026-10-31 session retro
  measured.** `CLAUDE.md` adds a delegate stall check (about 30 minutes with
  no commit and no message, and a re-check of every delegate after a context
  compaction), makes a permission-classifier denial final for every agent of
  the session, and puts the first Copilot review at about 5 minutes. The
  `open-pr` skill gains a hadolint gate for the Dockerfiles, tests for new
  code before the PR opens, the 16 real check names, the GraphQL request for
  a further Copilot round, a `git pull --ff-only` of the shared checkout after
  a merge, and a report of worktrees whose branch is gone. `zweitmeinung`
  attaches a diff over about 60 KB instead of inlining it, documents how
  `--attach` resolves paths, and states the measured Gemini costs. Gate
  commands name ruff's `dev` extra (`uv run --extra dev ruff …`), which a
  fresh worktree lacks.
- **Recipes that lived only in chat are documented.** The single-library
  `impl-generate.yml` dispatch with its optional inputs
  (`docs/workflows/overview.md`), the eval-matrix forms real runs use
  (`agents/README.md`), and the export, edit and import route for a
  second-generation Cloud Build trigger, whose `update github
  --included-files` fails with `INVALID_ARGUMENT`
  (`agentic/docs/project-guide.md`).
