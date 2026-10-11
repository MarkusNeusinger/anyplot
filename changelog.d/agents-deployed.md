### Changed

- **The agent network's two services are deployed.** The design doc, the
  agents README and the docs index now say that `anyplot-renderer` and
  `anyplot-agents` run in Cloud Run (europe-west4) since 2026-10-11, deployed
  by the `deploy-renderer` and `deploy-agents` triggers, and that owner tasks
  2, 8 and 14 are done except the API trigger's settings; the API side stays
  dark until the user-id secret exists and the API trigger sets the service
  URL and `_AGENT_ENABLED=true`. The recipes stay in the owner tasks for the
  record. (#12127)
