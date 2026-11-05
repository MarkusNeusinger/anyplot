### Added

- **`agent_turn_resumed`.** A Plausible event with `outcome` (`resumed`, `gone`, `failed`) counts every chat turn
  whose stream was cut after its first event, and whether the page read its result anyway. The origin's logs cannot
  see a cut between the browser and the edge, so this event is how often it happens.

### Fixed

- **A cut chat stream no longer hides a plot the server made.** On 2026-11-05 an HTTP/3 error ended a chartjs turn's
  stream 104 s into a 126 s run. Both origin hops ran the turn to its end and stored version 1, but the page showed
  "the server did not answer", and the retry made a version 2. Now every turn event carries the SSE id
  `<run_id>.<n>`, and the session keeps its latest turn's events. A new `GET /agent/session/turn` (and
  `/debug/agent/sessions/{sid}/turn`) with `Last-Event-ID` streams the rest of the turn, live until it ends. When a
  stream fails or ends without `done`, the page keeps the loader with a quiet "connection lost · reconnecting…" line
  and reads the turn again after 1, 2, 4 and 8 s. It shows the error only when every read failed, and the next click
  of the same request reads that turn first instead of making the same plot twice. The agents stream now writes a
  `: ping` after every 15 s without an event, as the BFF route already did, and a test pins the BFF's ping. A client
  that the agents service sees go still cancels the run.
