### Added

- **A promoted feedback case replays only where its sender was told it would
  go.** Until the deploy of 2026-11-18 the consent line under the chat's
  feedback form named no AI recipient besides Claude by Anthropic on Vertex AI
  in the EU, yet `python -m agents.evals.matrix --provider gemini` or
  `--location global` replayed such a case's data elsewhere without a word. A
  promoted case sent before 2026-11-19T00:00:00Z now replays only on Claude
  through Vertex AI in location `eu` (any Claude model there), and so does a
  case that corrects one sent before then, one step deep, because a session
  lives in one page load. A later case, a case from the admin lane, a case
  marked with `import_case.py --owner-chat` as holding the operator's own data,
  and every committed fixture replay anywhere; the admin lane says who held
  the admin door, not whose data was pasted. `import_case.py` and
  `sync_cases.py` record in `case.json` the manifest's `created_at` as
  `sent_at`, the lane its `user_hash` names (`admin` or `public`, by the exact
  form the BFF gives each lane's ids; the value itself is never copied), and
  the second the corrected case was sent (`replaces_sent_at`, never its id);
  the sync never sets the owner mark. The check fails closed: a case without
  those fields (every case imported before, every saved session), with a send
  time later than now, or with a `user_hash` of neither form is pinned, and a
  case under the fixtures that carries them is refused. It sits in
  `cases.select_cases`, so every tool that selects eval cases names the routes
  of every model it calls, resolved from the settings after flags, environment
  and defaults (root, adapter, reviewer and judge; on `claude-cli` the root's
  chat goes to Vertex AI and the others do not; an `ANTHROPIC_VERTEX_BASE_URL`
  takes every Claude call elsewhere), and matched against the agents as they
  were built. A run that would leave the pin ends with exit code 2 before the
  preflight and names each pinned case, the pinned route and each of the
  run's routes with what takes it off the pin; `--skip-pinned` runs the rest,
  prints the left-out ids to stderr and records only their count, and such a
  run is never saved as a baseline. Each run record now carries the fields the
  rule reads, so `score.py` applies the same rule to the renders
  `--keep-attempts` kept, also for a case that has left `.cases/` since, pins
  the promoted runs of an older report, and reads only the cases its admitted
  runs name. A test in the API's tree holds the two lane forms to the routes
  that write them.
- **No test reads the promoted cases any more.** Four eval tests (two static
  runs of `matrix.main`, its no-match exit and a preflight's smoke pick)
  called `load_cases()` with its default, which was bound at import to the
  real `agents/evals/.cases/`, so in a checkout that holds promoted cases a
  test run read a visitor's data into memory, and four tests outside the eval
  folder walked all of `agents/` with `rglob` and so listed its entries. The
  default is now read on each call (`import_case.promoted_cases_dir`), an
  autouse fixture points it at an empty temporary directory for every eval
  test, and `import_case.guard_promoted_dir` refuses the real directory,
  through the default or a directory a caller names, in any spelling
  (relative, with `..`, a string, a symbolic link, a path inside it), in any
  process that has imported pytest or that a test started
  (`PYTEST_CURRENT_TEST`), before anything reads it. The four walks read the
  tracked files from `git ls-files` instead.
