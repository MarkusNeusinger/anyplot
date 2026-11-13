### Changed

- **An off-topic question no longer brings a chat closer to closing.** In
  the chat of "Use with my data", every refusal by the scope check counted
  toward closing the session, and the third closed it. In a test round a
  wrongly refused question was a user's second refusal and came with the
  warning that one more would close the chat. Now only a message the check
  reads as an attempt to misuse the service counts: an off-topic question
  is refused and nothing else happens. Three such attempts still close a
  session, the warning before the last one stays, and the per-user strikes
  with their lock-out for the day are unchanged. The session stores such a
  message under a marker of its own for the count; the scope check's own
  context reads it as before. (#13082)
