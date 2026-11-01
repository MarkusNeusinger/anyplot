### Changed

- **`.plot_all()` plots the confirmed data, whatever its origin.** The admin
  fan-out of the agent chat (`/debug/agent`) has the agents service copy the
  page session's confirmed current data version into each library's session
  (`POST /v1/sessions/{sid}/dataset/copy`), byte for byte with its bindings,
  their confirmation and the session language, instead of posting the paste
  again. A table the assistant changed or computed (`sin x cos x`) now fans
  out too, and every library plots exactly what was confirmed. Both sessions
  must be the caller's, the target a fan-out session without data, the source
  confirmed; a copy parses and judges nothing again, counts as no paste, and
  has a per-user limit of its own. While the panel is open the data card
  waits, so every library copies the same confirmed data. The page falls back
  to posting the paste again while the server has no copy route. (#12501)

### Fixed

- **The agent chat's URL follows the session.** A library switch writes the
  library's `language` next to `library`, so the query no longer reads
  `library=matplotlib&language=javascript`, and the header's `all` pill is in
  the URL as `&all=1`, which a reload presses again once the libraries are
  known. (#12501)
