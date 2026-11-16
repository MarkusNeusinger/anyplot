### Changed

- **Only a matching render hash lets a review run.** A staged `render.sha256`
  that is missing, holds no hash, or has one line and doesn't fit now stops
  `impl-review.yml` like a mismatch does: nothing is scored and no header is
  committed. A first generation is parked with the label
  `ai-render-unverified` (it replaces `ai-render-mismatch`, which no PR had
  carried yet), and a gated regeneration is kept with the new returning code
  `render_unverified`. A hash that couldn't be downloaded after three attempts
  isn't a finding about the renders: a first generation then ends as a failed
  review that the watchdog starts again once, and a regeneration is kept. The
  check also reads the gcloud storage wording of a missing object as "no
  hash".
- **A run that can't stage `render.sha256` fails.** The hash write is its own
  step in `impl-generate.yml` and `impl-repair.yml`, last and fatal, so no PR
  reaches its review without a hash. In impl-generate the failure counts as an
  infrastructure failure: the pair is generated again without spending one of
  its three attempts. In impl-repair it takes the repair's crash path, and the
  comment names it.

### Fixed

- **The generation retry cap holds when the failure count can't be read.**
  "Handle generation failure" piped `gh api` into `awk` and relied on a shell
  option that GitHub Actions doesn't set by default, so a failed count read
  as zero earlier failures and bought another full generation. The call's own
  exit status now decides, and the handler's tests also run under plain
  `bash -e`.

### Removed

- **The `/update` command.** Its ship phase uploaded a `plot.png` that nothing
  produces, to a staging path the review doesn't read, and expected a repair
  loop its PR never got. A locally written implementation goes through the
  pipeline's adopt mode instead, as the catalogue audit already does.
