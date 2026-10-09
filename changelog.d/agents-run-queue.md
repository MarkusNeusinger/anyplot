### Added

- **A run queue in front of every agent chat turn.** The anyplot-agents
  service now runs one pipeline run at a time (`AGENT_RUN_CONCURRENCY`, 1)
  and starts at most one a minute (`AGENT_RUNS_PER_MINUTE`, 1, a sliding
  window), so one 4 GiB instance never holds more than the one sandbox that
  spikes S and S2 showed it serves safely. A turn waits at most
  `AGENT_QUEUE_MAX_WAIT_S` (600 s) and the queue holds as many turns as that
  wait allows (10); past that the turn gets `503 capacity`, or
  `error{code:"capacity"}` when it waited the maximum. While it waits, the
  stream sends `status{step:"queued", position, waiting}` and the request
  deadline has not started; `GET /v1/status` reports `waiting` and
  `in_flight`, and a user with a queued turn gets `409 run_active` like one
  with a running turn. A user already over the daily token budget gets the
  `budget` refusal at once instead of a place in the queue. A `premium` lane
  goes before the normal one but nothing sets it yet.
- **Serial renders for every backend.** `AGENT_RENDER_CONCURRENCY` now
  defaults to 1 and is enforced in one place, `SerialRenderer` in front of
  whichever backend renders, one theme per slot, so the sandbox, local and
  fake backends cannot run two renders at once. A freed slot goes to a
  waiting pipeline render before a waiting theme toggle.
- **One theme per run, and a theme toggle that costs no tokens.** A run
  renders and reviews only the theme the user asked for (light unless they
  ask for a dark plot), so the host gates, the reviewer's defect lines, the
  padded fallback, the artifacts and the exported `plot.py` run line all name
  that one theme. `POST /debug/agent/sessions/{sid}/versions/{version}/render
  {theme}` (and its `/v1` original) renders the other theme of a finished
  version from its stored code and data through the render backend and the
  host gates, with no adapter, no reviewer and no queue, and answers `ok`,
  `needs_attention` (a padded canvas) or `failed` with the version's
  artifacts. A toggle and a turn refuse each other in a session, a user has
  one run or toggle in flight, a toggle waits at most 120 s for the render
  slot, and a theme that failed the host gates is rendered at most twice.
- **A hard cap on one relayed chat turn.** The BFF ends a turn by
  `AGENT_TURN_MAX_S` (590 s), below anyplot-api's 600-second request
  timeout, so every stream still ends with `error` and `done`: a turn still
  queued when its run could no longer finish inside the cap ends with
  `capacity` and leaves the queue before it spends a token.
