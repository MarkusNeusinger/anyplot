### Changed

- **The agents service keeps one instance warm.** `anyplot-agents` deploys with one minimum instance, so the first chat message after a quiet period no longer waits for a cold start, and sessions and day counters survive idle periods. Its idle cost of about 0.44 CHF a day falls inside the account's unused Compute Flexible commitment until 2027-01-15 (#12511).
