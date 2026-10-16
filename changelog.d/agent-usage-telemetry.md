### Added

- **Content-free usage telemetry for the agent chat.** The agents service writes four events,
  `data_input`, `chat_turn`, `pipeline_run` and `outcome`, one wide JSON line each, on a logger of
  their own with `log_type: "agent_telemetry"` for a Cloud Logging sink into a 180-day log bucket
  that BigQuery reads. Every field is a closed enum, a bucket, a count or an id from a closed set
  (strict pydantic models, parser warnings mapped to closed codes in
  `agents/anyplot/data/warning_codes.py`), the session is a salted per-process hash, no line carries
  the user id, and a canary test fails if a column name, cell, note, file name or message reaches a
  line. The page reports copies, downloads, saves and feedback through a new beacon
  (`POST /debug/agent/sessions/{sid}/outcome`), and the eval harnesses tag their lines `harness`.
  Committed BigQuery views (`agents/telemetry/views/`) deduplicate by idempotency key and add
  sessions with a 30-minute inactivity rule, usage, failures and cost; `docs/reference/agent-telemetry.md`
  lists the one-time setup. (#12205)
- **Agent usage card on `/debug`.** Sessions, plots shipped, kept and repair rates, and the top specs,
  input formats and refusal codes of the last 7 or 30 days, read through the new admin-only
  `GET /debug/agent-usage` (aggregates only; an empty state while `AGENT_TELEMETRY_DATASET` is unset). (#12205)
