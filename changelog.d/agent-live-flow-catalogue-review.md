### Changed

- **The agent's plot pipeline reviews with the catalogue rubric and proofreads itself.** The
  reviewer now scores each render with the catalogue rubric (the offline scorer's twin; the
  code decides from the points), every round is reviewed and the best-scored version ships,
  and before each review the adapter checks its own render against the rubric's technical
  rows, which never counts as a repair. A shipped plot at or above 95 % of the technical
  points shows without notes. The experiment switches behind it (`AGENT_REVIEWER_MODE`,
  `AGENT_REVIEW_BAR`, `AGENT_STATUS_BAR`, `AGENT_SHIP_BEST`, `AGENT_SELF_REVIEW`, and the
  highlight switches) stay settings.
- **A complicated plot gets the time and the tokens to finish.** The adapter and the
  reviewer think at high effort with 8,192 and 4,096 tokens of thinking room (2,048 cut 10
  of 80 first adapter calls on Vertex) and the root at medium; the pipeline's soft deadline
  rises from 140 s to 480 s (hard 540 s, Cloud Run timeouts 1200 s) and the per-request
  token budget to 800k, so a repair round is no longer skipped for time. A repair whose edits do
  not apply gets one retry in the same round, and an unreadable review is asked once more
  instead of shipping the render unreviewed.
