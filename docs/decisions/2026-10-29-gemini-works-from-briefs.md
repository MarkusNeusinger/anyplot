# Gemini takes larger packages from brief files, one pull request per task

- Date: 2026-10-29
- Proposed: every Gemini task needed its own labelled issue. A second opinion rejected a work order
  pasted into the session, which exists nowhere durable until Gemini's first push.
- Decided: he wanted to hand over larger packages with less ceremony, so Claude writes a read-only
  brief file outside both checkouts, where Gemini cannot commit it by accident and the acceptance it
  is judged against is not in the tree it edits. He had already let long tasks run their tests and
  builds unattended in his own session (2026-10-22), trusting Gemini to keep to the rules as he
  trusts Claude. On 2026-10-30 he set that a task ends in one draft pull request however many
  packages it has: every pull request costs a Copilot round, a changelog fragment, CI, a merge and a
  deploy.
- Where: #12458, #12462, `.claude/skills/gemini-task/SKILL.md`, `.claude/guardrails.md`
