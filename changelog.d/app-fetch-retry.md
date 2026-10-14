### Fixed

- **A transient network glitch no longer leaves a page empty.** A short edge or
  network failure (a request blocked without CORS headers, surfacing as
  "Failed to fetch") used to leave the homepage numbers at "—" and a plot page
  at "Failed to load spec" until a full reload. `apiGet` now retries network
  errors and 408/425/429/500/502/503/504 responses twice with backoff, honouring
  `Retry-After` and the caller's abort signal, while a 404 still fails at once
  and POSTs, the authenticated debug and agent-chat requests and the chat's
  stream never retry; the API exposes `Retry-After` to the page. If a load still
  fails, the plot page and the homepage numbers offer `.retry()`, which reloads
  the data in place. (#12174)
