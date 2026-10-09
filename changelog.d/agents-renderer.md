### Added

- **The anyplot-renderer service that runs adapted plot code in Cloud Run
  sandboxes.** `agents/renderer/` is a small FastAPI service with
  `POST /render` and `GET /status` behind Cloud Run IAM and the same
  ID-token claims check as the agents service. It runs every theme of a job
  in a sandbox of its own, one at a time, built on what spikes S and S2
  measured: no `--write` and no egress, an explicit `PATH`, every user byte
  on a 512 MiB in-memory volume with a host watchdog that kills a run past
  64 MiB, a kill that counts only once the launcher has exited, one retry
  when the launcher fails before the harness starts, bounded stdout and
  stderr, the rlimits 60 s CPU, 50 MiB per file, 1 GiB address space and 64
  processes, and `MemAvailable` as the memory signal. It only runs code; the
  host gates stay in the agents service. Its image installs the plotting
  libraries without ADK, and `agents/renderer/cloudbuild.yaml` builds it,
  deploys a candidate (creating the service on the first build), smokes it
  with an anonymous call and a real render, and promotes it.
- **A `remote` render backend, now the default.** `AGENT_RENDERER=remote`
  sends each render to `AGENT_RENDER_URL` with an ID token from the metadata
  server, or in development from `AGENT_RENDER_TOKEN` or the developer's
  Application Default Credentials, so a local `adk web` and the deployed
  agents service render in the same sandboxes. It retries once on a
  connection error or a Cloud Run front-end error and maps every other
  failure to a renderer error. The in-process `sandbox` backend stays as an
  unused stub.

### Changed

- **The probe harness reports its own start and end.** It prints a
  `HARNESS` start line before anything else and a closing line with its peak
  memory and CPU time, sets every limit soft and hard alike, takes optional
  address-space and process limits, and copies the image's baked matplotlib
  font cache into the sandbox before matplotlib loads.
