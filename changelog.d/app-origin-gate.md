### Security

- **The site's own origin has a gate now, and it ships switched off.** The API's
  shared-secret gate closed one of two doors; `anyplot-app` stood with
  `ingress=all` beside it, serving the whole site from its `*.run.app` URL with
  no bot challenge, no WAF and no rate limit — and relaying any crawler user
  agent through `@seo_proxy` into a repository query and a Plausible event.
  `app/origin-gate.conf.template` is the nginx half: the base image's own
  envsubst entrypoint renders the maps with the secret before nginx starts, and
  every server block refuses what the Cloudflare edge did not stamp.
  `ORIGIN_GATE` unset means off, `on` means 403, and armed with no secret fails
  CLOSED — the map keys are tagged so an empty value cannot become "match
  anything". Nothing is armed by merging: the rollout, the hostnames the
  Transform Rule has to cover and the rollback are in
  `infra/cloudflare/README.md`.

- **`X-Origin-Gate` on `/_health` makes arming a measurement rather than a
  leap.** The same five verdicts the API reports — `off`, `off-seen`, `ok`,
  `missing`, `mismatch` — for the request they were asked with, never the value.
  Ask every route into the container while the gate is still off and arm only
  once each one that must keep working reports the header arriving. The apex
  Worker's path cannot be asked that way, so `/api/event` reports it too: that
  is the one path the Worker sends to this container, a Worker subrequest skips
  its own zone's Transform Rules, and arming it blind would have answered every
  Plausible pageview on the site with a 403.

### Changed

- **The three callers that reach the app origin without the edge now carry the
  header themselves.** The pre-traffic smoke in `app/cloudbuild.yaml` reads
  `ORIGIN_SECRET` inside the step rather than through `availableSecrets`, which
  resolves at build start; `bot-serving-check.yml` sends it from the repository
  secret and reads `/_health` first, so a missing or half-rotated secret fails
  with a message naming itself instead of reporting ~36 crawler checks as a
  broken site; and the apex Worker stamps its `/api/event` branch. A `Host` rule
  would have been a real boundary here — `anyplot.ai` is a Cloud Run domain
  mapping, so `$host` does tell the edge from the raw URL — but the bot monitor
  cannot spoof a Host either, and any exception it could present instead is
  public with this repository.

### Added

- **CI builds the app image and runs the gate against it.** `app/Dockerfile` was
  hadolinted but never built before Cloud Build, which is after the merge — and
  what it produces is not a program that fails to import but an nginx whose
  config is now RENDERED at container start. The new job in `ci-image.yml` runs
  the real image three ways: off, armed, and armed with no secret, checking the
  403, the exempt path, each verdict, and that the secret reaches neither the
  refusal page nor the container log.
