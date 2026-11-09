### Added

- **Machine readers on the stats page.** A new tile right after the visitors
  strip shows, per UTC day of the last 28, the requests of crawlers and AI
  assistants that Cloudflare verified, split into reads for a person, AI index
  and training reads, and search engines, with the MCP requests of every client
  beside them and a footnote naming the unverified requests of named vendors
  that are not counted. It reads `GET /insights/machine-readers`, counts only,
  from the machine-read lines in BigQuery; a failed query answers
  `unavailable` and is never cached, so the tile recovers on the next load.
  The About page and the README point at it. (#13015)
- **A machine readers section on `/debug`.** `GET /debug/machine-readers`
  (admin, 7 or 30 days) answers every live line whatever its verdict, status
  or surface: the totals, one row per vendor and purpose with Cloudflare's
  category, the counts per surface, the 404s and its five most requested
  routes, and one row per day by audience. The section draws them as tiles, one
  matrix that opens a row to its routes, and a per-day table. (#13015)

### Fixed

- **No more claims that BigQuery's result cache answers repeated telemetry
  queries.** The linked `_AllLogs` view changes with every line, so the
  process caches are the only caches; `api/agent_usage.py` and
  `docs/reference/agent-telemetry.md` say so now. The trigger step of both
  telemetry setups uses the export, edit and import route, because
  `gcloud builds triggers update github` refuses the second-generation
  `deploy-api` trigger. (#13015)
