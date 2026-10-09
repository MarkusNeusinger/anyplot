### Added

- **Agent network design document.** `docs/concepts/agent-network.md` describes
  the planned "Use with my data" agent network on Google ADK 2.11 and Gemini
  3.8 Flash through Vertex AI: the agent roster, the adapt, render and review
  pipeline, the two-profile code validator, the Cloud Run sandbox renderer, the
  guardrail layers, quick-feedback capture, a model-version regression harness,
  serving on a separate Cloud Run service behind the `/debug` gate, the phased
  roadmap with spikes and exit criteria, and the owner tasks. Design only; no
  code ships with it, so the decisions are reviewable before anything is built.

### Fixed

- **Retest workflow records the action pin it actually runs.** The Dependabot
  bump of `claude-code-action` updated the `uses:` pins of `impl-review.yml`
  and `review-retest.yml` but not the workflow-level `ACTION_SHA` that the
  retest records write into every record, so the unit test that keeps the two
  aligned failed on `main` without CI noticing (the Dependabot PR ran no
  tests). `ACTION_SHA` now matches the pinned action again.
