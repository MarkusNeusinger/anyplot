### Added

- **Review retest harness.** A new dispatch-only workflow,
  `.github/workflows/review-retest.yml`, re-runs the AI quality review on a
  frozen set of implementations and regeneration pairs, several fresh sessions
  per item, for one rules version (`rules_ref`), and reports the pooled score
  spread, verdict flips at 90, weakness-topic agreement, the gate's verdict
  stability and order bias (regen pairs run in both orders), and — once the
  labels are confirmed — named-defect misses and false alarms, with a
  bootstrap comparison against a baseline arm and a snippet for the PR body.
  A review-rubric change used to be observable only on real pipeline runs;
  now it can be measured before it merges. The workflow is measurement-only:
  read-only job tokens without `id-token`, sessions that may not run `gh`,
  `git push` or `git commit`, and nothing written to a PR, an issue, a label,
  `plots/` or GCS. It refuses while the production pipeline is busy and caps
  a run at 240 sessions. The harness is `automation/scripts/review_retest.py`
  (with the pure metrics in `review_retest_metrics.py`); set v1 is
  `automation/retest/set-v1.yaml` (15 fresh core items, one per library, and
  7 core regen pairs including three identity controls), and its renders are
  frozen as public objects under `gs://anyplot-images/retest/sets/v1/` by the
  owner-authorized `review_retest.py freeze`. The same script's `gate-report`
  aggregates the production regen gate records. How to run and read it:
  `docs/workflows/review-retest.md`.
