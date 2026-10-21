### Fixed

- **Two merges in a row no longer leave production on the older commit.** Two
  builds of the same service deployed side by side, the later deploy moved the
  shared `candidate` tag, and the other build's smoke refused to promote; when
  that was the newer commit's build, the service stayed on the older one until
  the trigger was rerun (`deploy-app` on 2026-10-16 and 2026-10-21, `deploy-api`
  and `deploy-agents` on 2026-10-12). A `wait-turn` step in all four Cloud Build
  configs (`scripts/cloudbuild-wait-turn.sh`) now holds each deploy until every
  older build of the same service has finished, so the newest commit deploys
  last; image builds still run in parallel. (#12222)
