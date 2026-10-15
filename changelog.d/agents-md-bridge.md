### Added

- **Agent rules and skills for non-Claude agents.** `AGENTS.md` is a symlink to
  `CLAUDE.md` and `.agents/skills/` a symlink to `.claude/skills/`, so the
  Antigravity CLI (`agy`), Codex, and other tools that read those paths load the
  same rules and skills from one source instead of a third file to keep in sync.
  A unit test fails if either link is replaced by a real file or points
  elsewhere.
