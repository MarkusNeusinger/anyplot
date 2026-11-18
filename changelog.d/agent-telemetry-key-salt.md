### Fixed

- **A telemetry line's idempotency key could be recomputed from the debug lines.** The key was a plain hash of the
  line's session hash, turn, event and an attempt label that often holds the request id, and the attribution
  lines carry that id as well: with both logs, a key could be recomputed per request id and a telemetry row
  joined to its debug lines by the key. The key is now an HMAC under the per-process salt of the session
  hashes, in a domain of its own (`agents/anyplot/telemetry.py` `idempotency_key`). Deduplication is unchanged:
  a line that Cloud Logging delivers twice or a pipeline node that ADK runs again keeps its key. Lines written
  before the change keep their plain keys, so for them, and through the session hash for the other lines of
  their sessions, the join stays possible while someone holds the request id; the debug lines hold it for 30
  days. `docs/reference/agent-telemetry.md` now also names the join by token counts, which this change does
  not close. (#13183)
