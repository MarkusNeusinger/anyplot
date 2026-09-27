### Changed

- **A pair's first implementation now runs on Opus, regenerations stay on
  Sonnet.** `impl-generate.yml` resolves the model per (spec, library) pair:
  Opus when the pair has no implementation file on `origin/main` yet, Sonnet
  when it already has one (Opus again for a forced regeneration with
  `regen_gate=false`, which takes the fresh-generation path), and threads the
  result into that PR's review and repairs as before. The `model` input on `impl-generate.yml`,
  `bulk-generate.yml` and `daily-regen.yml` now defaults to `auto` (the
  routing); `haiku`, `sonnet` or `opus` still pins one model for every pair.
  Label-triggered runs, the watchdog's generation retries and the babysit
  backfill scripts (`MODEL` now defaults to `auto`) follow the same routing,
  so a full-catalogue backfill now runs on Opus. The resolved model and its
  reason appear in the run summary and the issue preview comment, and the PR
  body records it (`**Model:** opus`). Review and repair rescues that arrive
  without a model (`impl-review-retry.yml`, the watchdog, a manual rerun)
  read that line back instead of falling back to Sonnet, so an explicit pin
  survives them. Without a readable `origin/main`, generation fails rather
  than guessing a first run. (#11947)
- **`bulk-generate.yml` paces dispatches 180 s apart for Opus runs.** The
  default pause is 180 s for model `auto` or `opus` and stays 120 s for a
  pinned `sonnet` or `haiku`; `pace_seconds` still overrides it. (#11947)
- **The daily-regen spec polish and similarity audit run on Sonnet instead of
  Haiku.** Both pre-flight steps in `daily-regen.yml` stay pinned regardless of
  the run's `model` input. (#11947)
