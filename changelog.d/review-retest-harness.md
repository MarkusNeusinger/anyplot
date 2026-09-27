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
  `plots/` or GCS; it has no effect until someone dispatches it. It refuses
  while the production pipeline is busy and caps a run at 240 sessions. The
  harness is `automation/scripts/review_retest.py` (with the pure metrics in
  `review_retest_metrics.py`). Set v1 is `automation/retest/set-v1.yaml`
  (15 fresh core items, one per library, and 7 core regen pairs including
  three identity controls, plus a full tier) and is frozen:
  `set-v1.lock.json` pins the sha256 of 94 public renders under
  `gs://anyplot-images/retest/sets/v1/`. The ground-truth labels ship as
  proposals and count only once the owner sets `labels: confirmed`. Every cell
  records the resolved model id, or none, and keeps the alias apart as
  `model_alias`, never in its place. The baseline arm (`rules_ref=0674ab6b5`)
  runs on today's harness: an overlaid `regen_gate.py` only receives the flags
  it already had. How to run and read it: `docs/workflows/review-retest.md`.
  (#11964)
- **Regen gate report.** `review_retest.py gate-report` aggregates the
  production regen gate records from the PR-comment markers: merge rate,
  reason codes, how far re-scored predecessors land from their stored scores
  (comparable decisions apart), the counted visible improvements, how often a
  review cites an "Expected, not a defect" bullet as an improvement, and soft
  alarms. (#11964)
- **A verification loop for review-rubric changes.** `CLAUDE.md` and the
  `open-pr` skill send pull requests that change the review rubric
  (`quality-criteria.md`, `ai-quality-review.md`, `default-style-guide.md`,
  the review rules in `prompts/library/*.md`, the review model routing) to a
  candidate arm of the retest, whose snippet goes into the PR body. (#11964)
