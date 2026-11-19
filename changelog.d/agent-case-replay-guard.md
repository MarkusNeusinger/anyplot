### Added

- **A promoted feedback case replays only where its sender was told it would
  go.** Until the deploy of 2026-11-18 the consent line under the chat's
  feedback form named no AI recipient besides Claude by Anthropic on Vertex AI
  in the EU, yet `python -m agents.evals.matrix --provider gemini` or
  `--location global` replayed such a case's data elsewhere without a word. A
  promoted case sent before 2026-11-19T00:00:00Z now replays only on Claude
  through Vertex AI in location `eu` (any Claude model there). A later case, a
  case from the admin lane, a case marked with `import_case.py --owner-chat` as
  holding the operator's own data, and every committed fixture replay anywhere.
  `import_case.py` and `sync_cases.py` record the manifest's `created_at` as
  `sent_at` in `case.json`, and the lane its `user_hash` names (`admin` or
  `public`, read from the exact form the BFF gives each lane's ids; the value
  itself is never copied); the sync never sets the owner mark. The check fails
  closed: a case without `sent_at` (every case imported before, every saved
  session) is pinned, and a `user_hash` of neither form names no lane. It sits
  in `cases.select_cases`, so every tool that selects eval cases names the
  routes of every model it calls, resolved from the settings after flags,
  environment and defaults (root, adapter, reviewer and judge; `claude-cli` is
  not Vertex AI). A run that would leave the pin ends with exit code 2 before
  the preflight and names each pinned case, the pinned route and each of the
  run's routes with what takes it off the pin; `--skip-pinned` runs the rest and
  the report counts what it left out. Each run record now carries `origin`,
  `sent_at`, `lane` and `owner_chat`, so `score.py` applies the same rule to the
  renders `--keep-attempts` kept, also for a case that has left `.cases/` since,
  and treats a report from before the change as pinned. A test in the API's
  tree holds the two lane forms to the routes that write them.
- **No test reads the promoted cases any more.** Four eval tests (two static
  runs of `matrix.main`, its no-match exit and a preflight's smoke pick)
  called `load_cases()` with its default, which was bound at import to the
  real `agents/evals/.cases/`, so in a checkout that holds promoted cases a
  test run read a visitor's data into memory. The default is now read on each
  call (`import_case.promoted_cases_dir`), an autouse fixture points it at an
  empty temporary directory for every eval test, and the resolver refuses the
  real directory in any process that has imported pytest, before anything
  reads it, so a test anywhere in the suite that reaches it without the
  fixture fails instead.
