### Changed

- **A feedback case no longer records a hash of its session that a log
  could reproduce.** Each stored case keeps a 16-digit value for its chat
  session, so that a corrected submission replaces the earlier one and the
  debug page lists a session's cases together. That value was the plain
  SHA-256 of the session id, and the agents service's request log holds the
  session id for 30 days, so the value could be made again from the log and
  tied a case to that session's requests. It is now a key the agents
  service makes under its per-process salt, in a domain of its own, so it
  matches neither the log lines' session hash nor the telemetry's. The
  service sends it only when the feedback route asks (`with_case_key`): a
  session saved to a file never carries it, and the stored case holds it
  once, as its session hash. A session never outlives that salt, so every
  case of a session still gets the same key, and once the process is gone
  the key cannot be made again from a session id. An agents service from
  before the change sends no key; the API then keys the case under its own
  per-process salt and logs that it did. Stored rows are left as they are;
  theirs can be made again only while a log still holds the session id.
  Once, at the deploy, a correction does not replace its case: a case
  stored before it has the old value, so a correction sent after it stays
  beside it in the list. A case can still be matched to its session by
  time, which the telemetry reference now says. (#13179)
