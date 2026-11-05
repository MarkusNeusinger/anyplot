### Changed

- **Every release runs the agent evals first.** `/release` gains a step before the release PR
  opens: the prep and scope evals always, and the matrix smoke when the window changed the plot
  pipeline. The results go into the PR body as "Agent evals", and the next release compares against
  them. No CI job runs these suites, because they call the real models. A regression on main
  surfaced on 2026-11-05 only because a sibling PR happened to run its eval; a release is now the
  fixed point where every prompt and model change of the window is measured together. (#12579)
