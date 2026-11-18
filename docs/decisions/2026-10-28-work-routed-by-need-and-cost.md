# Work goes to a model by what it needs and costs, and a subagent that writes outside its worktree runs on Opus

- Date: 2026-10-28
- Proposed: the routing of work to models that he had set on 2026-08-11 and refined since.
- Decided: pick the agent by the work, and spend Claude tokens last: work that another lane can do
  well goes there first. A subagent that changes state outside its worktree, or makes judgment
  calls, runs on Opus; his reason: he does not trust the smaller models with writes. A second
  opinion from Fable and Gemini runs only when he asks for one, so a plan does not get one by
  default. On 2026-10-29 he added a check of every code pull request by Gemini 3.8 Flash before it
  opens.
- Where: #12429, `agentic/docs/agent-operations.md`, `.claude/guardrails.md` ("Pick the agent by the
  work"), `.claude/skills/zweitmeinung/SKILL.md` ("Who reviews")
