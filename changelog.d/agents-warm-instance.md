### Fixed

- **A cancelled local render waits for both theme containers.** It used to return, and remove the run directory, while the second container was still being killed, which also made a backend test flaky (#12511).

### Changed

- **The agents service keeps one instance warm.** `anyplot-agents` deploys with one minimum instance, so the first chat message after a quiet period no longer waits for a cold start, and sessions and day counters no longer vanish when Cloud Run scales the service to zero; a session still ends after an hour without activity (`AGENT_SESSION_IDLE_S`), and a deploy still resets both. Its idle cost of about 0.44 CHF a day falls inside the account's unused Compute Flexible commitment until 2027-01-15 (#12511).
