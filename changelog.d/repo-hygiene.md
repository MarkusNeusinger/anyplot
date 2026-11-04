### Changed

- **Model routing moves from `CLAUDE.md` to `agentic/docs/agent-operations.md`.**
  The subagent model tiers, the Gemini lane, the Gemini check before a code PR
  opens, and the second-opinion rule now live in the new document; `CLAUDE.md`
  keeps one rule that points to it and makes it binding, the two `agy`
  prohibitions, and the delegate-brief duties. No rule changes meaning, and
  `tests/unit/test_agent_instructions.py` pins the moved rules in their new place.
- **Comments say why, not who.** A new rule in `CLAUDE.md` and
  `.github/copilot-instructions.md`: provenance (who asked, which review found
  it, the date) goes into the commit or the PR, and code migrates on touch.
  Comments under `api/` and `app/src/` drop their reviewer names, owner-decision
  notes, and dates that only recorded when something was decided or found; dates
  that bound old data or date a measurement stay.
- **The map's ForceGraph2D instance is typed.** `ForceGraphHandle` names the
  methods the map calls instead of `any`, which removes the last two
  `eslint-disable` comments in `app/src`.
