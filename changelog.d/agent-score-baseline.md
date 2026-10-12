### Added

- **Agent results scored with the catalogue rubric.** `agents/evals/score.py` scores a
  harness run's first and shipped renders on Claude Opus 5.5 with the catalogue's own
  rubric, read verbatim from `prompts/quality-criteria.md` and the review prompt and
  restricted to the 16 criteria a user sees (`agents/anyplot/scoring.py`,
  `agents/anyplot/prompts/scorer.md`): the code adds up and applies the caps, and the
  report gives the score distributions, what repair 1 gains, the runs each threshold
  would send to an advisor, and the points lost by criterion. The harness keeps every
  attempt's render with `--keep-attempts`. It is the measurement behind the owner's
  quality ladder; the agent itself is unchanged.
