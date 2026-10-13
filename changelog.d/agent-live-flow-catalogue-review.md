### Changed

- **The agent's plot pipeline reviews with the catalogue rubric and proofreads itself.** The
  reviewer now scores each render with the catalogue rubric (the offline scorer's twin on
  Haiku; the code decides from the points), every round is reviewed and the best-scored
  version ships, and before each review the adapter checks its own render against the
  rubric's technical rows, which never counts as a repair. A shipped plot at or above 95 %
  of the technical points shows without notes. The experiment switches behind it
  (`AGENT_REVIEWER_MODE`, `AGENT_REVIEW_BAR`, `AGENT_STATUS_BAR`, `AGENT_SHIP_BEST`,
  `AGENT_SELF_REVIEW`, and the highlight switches) stay settings.
