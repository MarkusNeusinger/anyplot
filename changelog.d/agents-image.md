### Added

- **The anyplot-agents image and its Cloud Build deploy.** `agents/Dockerfile`
  builds the private `/v1` service on `python:3.13-slim` with the `agents`
  extra and no plotting extra, because every render goes to anyplot-renderer.
  It copies the source tree rather than a wheel, so the prompts,
  `refusals.yaml`, the footer-strip fonts and the catalogue prompt sources sit
  at the paths the service reads them from. It runs as uid 1000 and fails its
  own build when one of those files is missing, the judge rubrics that the
  service reads only on first use included.
  `agents/cloudbuild.yaml` deploys it with the renderer's steps: a `candidate`
  revision without traffic (the first build creates the service), a smoke on
  the tag URL, and a promote of exactly that revision. The smoke expects
  exactly `403` from Cloud Run IAM for an anonymous `GET /v1/status`, then
  calls it with an ID token of the service account and checks the reported
  provider, model, location and libraries. The deploy uses one instance, 2 vCPU
  and 4 GiB, a concurrency of 20 and a 900 s timeout for the run queue's open
  streams, no sandbox launcher, and `--update-env-vars` only. The provider, the
  models and the libraries are substitutions, so a deploy switches the model
  arm without a code change, while the budgets stay at the settings defaults.
  The deploy refuses to run without the renderer's URL, and it always lets
  anyplot-api's identity and the smoke's account call the service. The config's
  header lists the owner's bootstrap steps.
- **A CI job that builds and smokes the agents image before merge.**
  `ci-image.yml` builds `agents/Dockerfile` when the service, `core/`, the
  catalogue prompts it reads or the dependency lock change. It checks that
  `/v1/status` reports the configuration its environment sets, that the
  production default refuses an anonymous caller with `401`, that the prompts
  and fonts are in the image and the eval cases are not, and that the service
  runs as uid 1000. `tests/unit/agents/test_image.py` holds the Dockerfile's
  COPY list, its build check and the root `.dockerignore` against every file
  the service reads, and the deploy's substitutions and variables against the
  settings; it also runs the deploy step's script against a fake `gcloud`.
