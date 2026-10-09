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
  with a running turn. A `premium` lane goes before the normal one but
  nothing sets it yet. Renders stay serial: `AGENT_RENDER_CONCURRENCY` now
  defaults to 1.
- **One theme per run, and a theme toggle that costs no tokens.** A run
  renders and reviews only the theme the user asked for (light unless they
  ask for a dark plot), so the host gates, the reviewer, the padded fallback
  and the artifacts all name that one theme. `POST
  /debug/agent/sessions/{sid}/versions/{version}/render {theme}` (and its
  `/v1` original) renders the other theme of a finished version from its
  stored code and data through the render backend and the host gates, with
  no adapter, no reviewer and no queue, and answers `ok`, `needs_attention`
  (a padded canvas) or `failed` with the version's artifacts.
