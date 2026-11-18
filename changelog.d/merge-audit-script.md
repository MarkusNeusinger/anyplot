### Added

- **A script audits a branch's merge commits for dropped content.**
  `.claude/skills/open-pr/scripts/merge_audit.py` redoes every merge
  commit of a branch mechanically and reports what one side added and
  the committed merge no longer has: a line dropped outside a conflict,
  which is the mark of a whole file taken with `git checkout --ours`,
  or a file without any conflict that still differs. `CLAUDE.md` and
  Copilot's guide now say to resolve a conflict inside its markers and
  to run the audit after a merge that had one; `/open-pr` carries the
  step, and the guardrails hold the incident behind it.
