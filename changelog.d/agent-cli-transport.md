### Added

- **Agent experiments on the Claude subscription.** `AGENT_TRANSPORT=claude-cli`
  (development and test only) sends the agents' Claude calls through the local Claude Code
  CLI instead of Vertex AI, below ADK, so an experiment runs the live code unchanged:
  agents, prompts, plugins, pipeline, the deployed renderer and the gates. The root's chat
  with tools stays on Vertex AI. `AGENT_ADAPTER_MODEL` and `AGENT_REVIEWER_MODEL` pick a
  model per agent, `scripts/agents-experiment.sh` runs the harness and the rubric scorer
  in one command, and `agents/evals/score.py --transport claude-cli` and the ladder lab
  use the same transport.
