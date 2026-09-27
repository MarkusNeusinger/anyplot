### Changed

- **A pair's first implementation now runs on Opus, regenerations stay on
  Sonnet.** `impl-generate.yml` resolves the model per (spec, library) pair:
  Opus when the pair has no implementation file on `origin/main` yet, Sonnet
  when it already has one, and threads the result into that PR's review and
  repairs as before. The `model` input on `impl-generate.yml`,
  `bulk-generate.yml` and `daily-regen.yml` now defaults to `auto` (the
  routing); `haiku`, `sonnet` or `opus` still pins one model for every pair.
  Label-triggered runs, the watchdog's generation retries and the babysit
  backfill scripts (`MODEL` now defaults to `auto`) follow the same routing.
- **The daily-regen spec polish and similarity audit run on Sonnet instead of
  Haiku.** Both pre-flight steps in `daily-regen.yml` stay pinned regardless of
  the run's `model` input.
