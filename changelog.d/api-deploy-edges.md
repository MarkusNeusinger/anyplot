### Changed

- **The API deploy gets the three edges the frontend deploy already had** — the candidate
  rollout `api/cloudbuild.yaml` invented was then improved in `app/cloudbuild.yaml` (#11207)
  and the improvements never came back. Three of them do now. `:latest` waits on `promote`
  instead of on `build-image`: it used to reach the registry before the candidate had been
  deployed, let alone smoked, so a build whose smoke failed still left `:latest` naming the
  image that failed it. The smoke re-asserts the `candidate` tag AFTER its probes as well as
  before — the tag is shared across builds, so a concurrent one could move it mid-smoke and
  this build would promote a revision it only believed it had probed; a competing build only
  ever tags its own revision, so ours at both ends means the tag was never reassigned while
  the probes ran. That detects an observed reassignment rather than proving where a probe
  landed: `status.traffic` is control-plane state, and tag-URL propagation can lag it, which
  is the residual `app/cloudbuild.yaml` already documents at its own smoke step. And the
  probes stop piping into `grep -q`, which exits at the first match and SIGPIPEs
  curl — the form only ever passed because `-ceu` carries no `pipefail`, so a later hardening
  pass adding it would have turned every deploy red. They go through the same `expect` helper
  `app/cloudbuild.yaml` uses, which fetches to a file and names the probe and the missing
  needle when it fails; `/health` keeps a bare variant because reaching it without the origin
  header is exactly what its gate exemption has to prove. (#11212)
