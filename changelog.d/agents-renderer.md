### Added

- **The anyplot-renderer service that runs adapted plot code in Cloud Run
  sandboxes.** `agents/renderer/` is a small FastAPI service with
  `POST /render`, `POST /render/{job_id}/cancel` and `GET /status` behind
  Cloud Run IAM and the same ID-token claims check as the agents service. It
  runs every theme of a job in a sandbox of its own, one at a time, built on
  what spikes S and S2 measured: no `--write` and no egress, an explicit
  `PATH`, every user byte on a 512 MiB in-memory volume that the service
  requires on Cloud Run, a host watchdog that kills a run past 64 MiB,
  10,000 files or a 512 MiB `MemAvailable` floor, a kill that counts only
  once the launcher has exited, one retry when the launcher fails before the
  harness starts, bounded stdout and stderr, a cleaned probe, and the
  rlimits 60 s CPU, 50 MiB per file, 1 GiB address space and 64 processes.
  A caller that disconnects or cancels stops its sandbox, an unexpected
  error answers a JSON `500 internal` without its message, and a launcher
  that outlives its kill ends the instance so Cloud Run starts a fresh one.
  It only runs code; the host gates stay in the agents service. Its image
  installs the plotting libraries without ADK, CI builds it and renders a
  seaborn plot through the harness before merge, and
  `agents/renderer/cloudbuild.yaml` builds it, deploys a candidate (creating
  the service on the first build, and only when the service is not found),
  smokes it with an anonymous call and a real render, and promotes it. (#12115)
- **A `remote` render backend, now the default.** `AGENT_RENDERER=remote`
  sends each render to `AGENT_RENDER_URL` with an ID token from the metadata
  server, or in development from `AGENT_RENDER_TOKEN` or the developer's
  Application Default Credentials, so a local `adk web` and the deployed
  agents service render in the same sandboxes. It rides out a cold start by
  retrying connection errors and Cloud Run front-end 429 and 5xx answers
  after 1, 3, 8 and 15 seconds, asks the renderer to cancel a render it
  abandons, and logs every failure it maps to a renderer error. When the
  renderer stopped a run at a limit, the repair feedback names the limit and
  the measured value. The in-process `sandbox` backend stays as an unused
  stub. (#12115)

### Changed

- **The probe harness reports its own start and end.** It prints a
  `HARNESS` start line before anything else and a closing line with its peak
  memory and CPU time, sets every limit soft and hard alike, takes optional
  address-space and process limits, and copies the image's baked matplotlib
  font cache into the sandbox before matplotlib loads. (#12115)
- **The caller check reads the header Cloud Run verified.** The agents
  service and the renderer read `X-Serverless-Authorization` whenever a
  request carries it, because Cloud Run then checks only that header and
  passes `Authorization` through unverified. (#12115)
