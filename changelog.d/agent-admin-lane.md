### Added

- **An admin lane in the agents service's run queue.** The admin's runs,
  `.plot_all()` above all, get limits of their own: five in flight, no
  start-rate window, five per admin, and no per-user day caps or message
  minute (`AGENT_ADMIN_*`), so a 15-library fan-out no longer waits behind
  the public lane's one slot and one start a minute (about 20 minutes in the
  user test of 2026-11-01). The BFF asserts the tier with `X-Anyplot-Tier:
  admin` from the identity its admin gate verified; a missing or other value
  is the public tier, so public users keep exactly today's limits and the
  two services deploy in either order. `GET /status` reports the caller's own
  cap, and the fan-out panel follows it.

### Changed

- **The global daily token budget rose to 80,000,000.** It stays the runaway
  guard for every tier, admins included (24,000,000 before), and the Claude
  calls of root, adapter and reviewer retry a refused call four times instead
  of the SDK's two; a 429 that outlasts them ends the run as `busy`, which
  the page words as "the model service is busy; try again in a minute".
  The render gates run in a worker thread, so one run's PNG checks never
  stall the other runs in flight.
