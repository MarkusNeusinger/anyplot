### Fixed

- **The unit tests run when an agent instruction file changes, and main is green
  again.** #12493 added the section "Long-running work reports progress
  proactively" to `.claude/guardrails.md` but changed no Python, so "Run Tests"
  skipped it and `test_every_companion_section_is_registered` failed on main.
  The section and the classifier-denial rule are now registered with their
  CLAUDE.md anchors, and `ci-tests.yml` also runs the tests for changes to
  `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`,
  `.claude/guardrails.md`, `.claude/skills/` and `agentic/commands/`, which
  `tests/unit/test_agent_instructions.py` and `tests/unit/skills` read. (#12494)
