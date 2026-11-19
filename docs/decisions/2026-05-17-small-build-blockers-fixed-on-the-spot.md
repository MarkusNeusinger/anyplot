# A small build or test blocker is fixed on the spot, even outside the task

- Date: 2026-05-17
- Proposed: #6961 listed a TypeScript error under "Out of scope" and left it for later. It broke
  the next production build, so that pull request's frontend fixes never reached anyplot.ai, while
  every check on it was green.
- Decided: recorded on 2026-05-17. An agent fixes a small build or test blocker on the spot, in the
  same pull request or a tiny follow-up, even when it lies outside its task. The AI workflow page
  counts it among the corrections that became rules.
- Where: #7052, `docs/concepts/ai-workflow.md`, `CLAUDE.md`
