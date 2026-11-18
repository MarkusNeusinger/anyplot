### Changed

- **A feedback case no longer records a hash of its session that a log
  could reproduce.** Each stored case keeps a 16-digit value for its chat
  session, so that a corrected submission replaces the earlier one and the
  debug page lists a session's cases together. That value was the plain
  SHA-256 of the session id, and the agents service's request log holds the
  session id for 30 days, so the value could be made again from the log and
  tied a case to that session's requests. It is now a key the agents
  service makes under its per-process salt and sends with the session
  bundle (`session.case_key`), under a domain of its own, so it matches
  neither the log lines' session hash nor the telemetry's. Session and salt
  end with the same process: every case of a session still gets the same
  key, and afterwards nobody can make it again. Until both services run the
  change, the API falls back to a hash under its own per-process salt.
  Stored rows are left as they are; theirs can be made again only while a
  log still holds the session id. A case can still be matched to its
  session by time, which the telemetry reference now says.
