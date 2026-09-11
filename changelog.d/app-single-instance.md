### Changed

- **`anyplot-app` runs as a single instance with concurrency 80 (was max 3,
  concurrency 15).** A static nginx never needed a second instance for capacity —
  its files answer in milliseconds and it sits at 15 MiB of memory — yet every
  crawler burst filled the 15 slots and started one or two more instances (50
  AUTOSCALING starts in the ten days to 2026-09-10), because nginx holds a
  proxied bot request open for as long as the API takes to answer. With the API
  on one warm instance those waits are milliseconds, and one nginx with 80 slots
  absorbs the burst without a cold start. `min-instances` stays 0; the API behind
  it caps its own work at 40 in flight.
