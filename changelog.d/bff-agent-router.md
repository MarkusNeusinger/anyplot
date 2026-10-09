### Added

- **Agent chat BFF under `/debug/agent`, shipped dark.** `api/routers/agent.py`
  puts the admin-only routes of the planned "Use with my data" chat in front of
  the private anyplot-agents service: status, eligibility, sessions, dataset,
  bindings, messages, cancel, artifacts, and delete. They sit behind the
  existing `/debug` admin gate, a kill switch (every route answers 404 until
  `AGENT_ENABLED` is on and both `AGENT_SERVICE_URL` and `AGENT_USER_ID_KEY`
  are set), and a CSRF guard (`X-Anyplot-Client` header, Origin check, JSON
  bodies). The agents service sees an HMAC user id, never an email; request
  bodies are allowlisted; a catalogue snapshot comes from the database; and the
  chat stream is re-framed into the `anyplot/1` SSE events, so unknown events,
  `error_details`, and stack traces never reach the browser, and every stream
  ends with `done`. `require_admin_identity()` now returns who passed the admin
  gate, and `require_admin` wraps it unchanged. The deploy writes
  `AGENT_ENABLED=false` and its smoke test expects 401 on
  `/debug/agent/status`; the routes are documented in `docs/reference/api.md`.
