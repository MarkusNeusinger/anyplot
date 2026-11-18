### Fixed

- **A telemetry line's idempotency key could be recomputed from the debug lines.** The key was a plain hash of the
  line's session hash, turn, event and an attempt label that often holds the request id, and the attribution
  lines carry that id as well: with both logs, a key could be recomputed per request id and a telemetry row
  joined to its debug lines, which the salted session hashes exist to prevent. The key is now an HMAC under the
  same per-process salt, in a domain of its own (`agents/anyplot/telemetry.py` `idempotency_key`). Deduplication
  is unchanged: a line that Cloud Logging delivers twice or a pipeline node that ADK runs again keeps its key.
  Lines written before the change keep their plain keys, so the join stays possible for them until their debug
  lines age out after 30 days.
