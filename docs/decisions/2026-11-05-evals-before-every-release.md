# Every release runs the chat's evals first

- Date: 2026-11-05
- Proposed: the evals call the real models, so no CI job runs them. On 2026-11-05 a regression on
  `main` surfaced only because a sibling pull request happened to run its eval. A scheduled workflow
  was the other way to run them.
- Decided: the evals are a duty of every release, not a scheduled workflow: the prep and scope
  evals always, the matrix smoke when the window changed the plot pipeline. A release waits when a
  suite fails its own gate, or when the prep eval lands more than three cases below the previous
  release.
- Where: #12579, `agentic/commands/release.md`
