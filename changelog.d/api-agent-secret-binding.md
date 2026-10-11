### Changed

- **The API binds the agent user-id secret.** `api/cloudbuild.yaml` adds
  `AGENT_USER_ID_KEY` to the secrets of `anyplot-api`, so the `/debug/agent`
  routes can derive their user ids. Together with `_AGENT_ENABLED=true` and
  `_AGENT_SERVICE_URL` on the deploy-api trigger (set on 2026-10-11), this
  switches the admin-only agent chat on in production.
