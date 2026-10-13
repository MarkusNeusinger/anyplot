### Added

- **Ladder lab for the agent's repair loop.** `agents/evals/ladder_lab.py` compares, on
  the same seed renders, how much the Opus scorer moves on one render, which rubric
  deductions Haiku, Sonnet, Opus and today's reviewer name, and which repairer and
  feedback form (defect lines, lines plus suggestions, a Sonnet or Opus advisor's plan)
  lifts the score. Every model call goes through the local Claude Code CLI with the
  agent's own prompts and schemas, and every answer through the pipeline's own edit,
  validator, render and gate code (#12158).
