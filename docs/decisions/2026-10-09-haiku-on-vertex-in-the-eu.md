# The chat's agents run on Claude Haiku 5.5 through Vertex AI in the EU

- Date: 2026-10-09
- Proposed: the first design of the agent chat, written to his answers of that time, pinned
  Gemini 3.8 Flash.
- Decided: Claude Haiku 5.5 on Vertex AI, location `eu`, is the default for every agent and for the
  guard judges. Gemini 3.8 Flash stays a second arm behind a switch, so the two can be compared on
  price and quality.
- Where: #12099, #12111, `docs/concepts/agent-network.md` (row "Model")
