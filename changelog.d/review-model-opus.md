### Changed

- **Every quality review runs on Opus.** `impl-review.yml` now reviews on Opus
  whatever model generated the implementation, so a regeneration (generated on
  Sonnet) is judged, and its predecessor re-scored, on Opus. The `model` input
  still chooses the generation and repair model; a manual review can pin
  another model with the new `review_model` input. The retest harness's
  `models=production` now runs every cell on Opus.
