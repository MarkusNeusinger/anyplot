### Changed

- **Only a matching render hash lets a review run.** A staged `render.sha256`
  that is missing, holds no hash, or has no code hash and doesn't fit now
  stops `impl-review.yml` like a mismatch does, and so does an implementation
  that can't be read at the PR head: nothing is scored and no header is
  committed. A first generation is parked with the label
  `ai-render-unverified`, the one label for every such stop, and a gated
  regeneration is kept with the new returning code `render_unverified`. A hash
  that couldn't be downloaded after three attempts isn't a finding about the
  renders: a first generation then ends as a failed review, which the watchdog
  starts again once unless it already rescued that PR, and a regeneration is
  kept. The check also reads the gcloud storage wording of a missing object as
  "no hash", and its PR comment prints a command only for a spec ID and a
  library name of the expected shape. The weekly regeneration review doesn't
  count a render-hash keep as a missing pair artifact: no review ran, so
  there is no pair to stage. (#13129)
- **A run that can't stage `render.sha256` fails.** The hash write is its own
  step in `impl-generate.yml` and `impl-repair.yml`, last and fatal, with five
  upload attempts, so a run that can't stage the hash never hands its PR to
  the review. In impl-generate the failure counts as an infrastructure
  failure: the pair is generated again without spending one of its three
  attempts. In impl-repair it takes the repair's crash path, and the comment
  names it. (#13129)

### Fixed

- **The generation retry cap holds when the failure count can't be read.**
  "Handle generation failure" piped `gh api` into `awk` and relied on a shell
  option that GitHub Actions doesn't set by default, so a failed count read
  as zero earlier failures and bought another full generation. The call's own
  exit status now decides, after three attempts, and the handler's tests also
  run under plain `bash -e`. (#13129)
- **The watchdog's review rescue can no longer remove a fresh failure
  label.** After it re-dispatched a failed review, the watchdog removed
  `ai-review-failed` itself. A replacement review that failed again within
  that moment had its new label taken away, and the PR was left with the
  rescue marker alone, which no rescue case sees. The rescue now only adds
  `ai-review-rescued`; the review it dispatched removes the old label when
  it starts, as every review does. (#13129)

### Removed

- **The `/update` command.** Its ship phase uploaded a `plot.png` that nothing
  produces, to a staging path the review doesn't read, and expected a repair
  loop its PR never got. A locally written implementation goes through the
  pipeline's adopt mode instead, as the catalogue audit already does.
  (#13129)
