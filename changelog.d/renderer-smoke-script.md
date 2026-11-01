### Fixed

- **The renderer deploys again, with plotly and bokeh.** Cloud Build refused the renderer's
  deploy for PB-2a before its first step ran, because the inline smoke step had grown to
  11,347 characters and Cloud Build accepts at most 10,000 per step argument; the agents
  service deployed and the renderer kept its previous revision. The render probes now live
  in `agents/renderer/deploy_smoke.sh`, which the smoke step calls with the token in the
  environment, a new unit test keeps every Cloud Build config's arguments under the limit,
  and `ci-tests.yml` runs the unit tests when a Cloud Build config or the smoke script
  changes.
