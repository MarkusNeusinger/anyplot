### Added

- **`.save()` downloads an agent chat session as one JSON file.** The chat
  header's new button saves the feedback case the agents service already
  assembles (the conversation, every version's code, plan, result and PNGs, the
  data profile, the bindings and the config stamp), with each version's
  `data.csv` while `# include data.csv` is ticked, the phase-1 default for
  admins. A session can now be kept and shown to whoever tunes the assistant
  before the stored feedback cases exist. The BFF's new
  `GET /debug/agent/sessions/{sid}/bundle?include_data=&version=` relays the
  agents service's bundle as an attachment (`anyplot-session-<id>.json`) behind
  the same admin gate, ownership and error mapping as the other session routes;
  it reads the bundle whole and refuses one over 32 MiB as `502 too_large`,
  because that is Cloud Run's limit on a response that is not streamed, so a
  larger file could not arrive whole anyway. Analytics:
  `agent_session_saved{include_data}`.
