# Work goes to a model by what it needs and costs, and only Opus writes outside its worktree

- Date: 2026-10-28
- Proposed: the Anthropic weekly limit runs out long before his Google AI Ultra quota.
- Decided: the work is split by what it needs, and work that Google's quota can do goes there
  first. A subagent that changes state outside its worktree, or makes judgment calls, runs on Opus;
  his reason: he does not trust the smaller models with writes. On 2026-10-29 he added a check of
  every code pull request by Gemini 3.8 Flash before it opens.
- Where: #12429, `.claude/guardrails.md` ("Pick the agent by the work")
