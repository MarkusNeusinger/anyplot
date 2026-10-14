### Changed

- **Agent chat answers at once; only sandbox work waits in the run queue.** A
  chat turn no longer enters the run queue or the one-start-a-minute rate
  window: a question, a refusal, `prepare_data` and `generate_data` answer
  right away, and only a `plot_pipeline` or `run_data_code` call takes the
  queue's slot and the turn's start, mid-turn, while the stream reports
  `status{step:"queued"}` and the request deadline pauses. A full queue now
  ends the turn with `error{code:"capacity"}` instead of `503 capacity` before
  the stream. To keep chat turns bounded, each user may send 10 messages a
  minute and 200 a day (`AGENT_USER_MESSAGES_PER_MINUTE`,
  `AGENT_USER_MESSAGES_PER_DAY`), checked before the scope judge and answered
  with the fixed `rate_limited` or `daily_limit` refusal, and a session closes
  at its third `out_of_scope` or `attack` refusal (`AGENT_SESSION_REFUSALS`;
  `needs_data` never counts), answering every later turn with
  `session_closed`. Owner decision of 2026-10-14, after a live test in which
  plain answers waited about 60 seconds each.
