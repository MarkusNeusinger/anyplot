### Fixed

- **A stale `ai-review-failed` no longer buys a second review.** When GitHub
  accepted a re-review dispatch but `gh` reported an error, `impl-review.yml`
  labeled the PR `ai-review-failed` beside the re-review that was already
  queued, and the watchdog's next scan dispatched another one. Every review
  run now removes the label when it starts, and the watchdog leaves such a PR
  alone while a review of it is queued or running, or drops the label when
  the PR already has a verdict. (#12041)
- **A verdict label that cannot be added fails the review run.** The early
  verdict step downgraded a failed `regen:kept` add to a warning, so the step
  succeeded without a verdict label and switched off the post-score rescue
  that keys on it. All four verdict labels are now added with three tries and
  fail the step when they do not land. (#12041)
- **The no-score review retry hands over to the watchdog when it cannot start.**
  "Validate review output" posted its retry marker and its dispatch without
  retries, and a failure there left the PR with no label at all. Both are now
  retried three times, the dispatch waits for the marker, and a failure ends
  in `ai-review-failed`. (#12041)
- **impl-repair's crash retry counts its marker across comment pages.** The
  budget read took the per-page counts of `gh api --paginate` as one number,
  so on a PR with more than 100 comments the one-retry cap never held. The
  pages are now summed, and a count that cannot be read counts as spent.
  (#12041)
