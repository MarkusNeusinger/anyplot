# Pull requests of the plot pipeline start no CI runs

- Date: 2026-11-01
- Proposed: every CI run on a pull request the plot pipeline opens waited for a human approval, sat
  with zero jobs until the merge, and then ended as a failure: 59 runs since at least 2026-10-24 that
  never checked anything and only left red marks.
- Decided: the CI workflows skip a pull request that changes only a plot's implementations and
  metadata; spec pull requests and any that touches another file keep every run.
- Where: #12499
