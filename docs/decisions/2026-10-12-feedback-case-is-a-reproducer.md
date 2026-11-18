# A feedback case is a reproducer to fix and retire, never an archive

- Date: 2026-10-12
- Proposed: quick feedback stores the case of a chat result in a bucket (#12139).
- Decided: his rule: a case is reported, triaged with a failure class, generalized into a code check
  or a synthetic fixture with invented data, fixed at its cause, and retired. On 2026-11-04 he set
  that triage runs in rounds when he asks for one, with no schedule.
- Where: #12551, #12139, `.claude/skills/triage-agent-cases/SKILL.md`
