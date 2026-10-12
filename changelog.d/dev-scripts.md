### Added

- **Scripts for the local agent stack and the PR loop.** `scripts/agents-dev.sh`
  starts the agents service, ADK's development UI, the API with the agent routes and
  the app, each against the real models and the deployed renderer, with the identity
  token renewed every 55 minutes and the API keys read from files that are never
  printed; `scripts/agent-cases.sh` reads the production feedback cases. The
  `open-pr` skill bundles the watchers it asks for: the PR's checks, the Copilot
  review rounds with their unresolved threads, and a merge's Cloud Build deploys
  (#12151).
