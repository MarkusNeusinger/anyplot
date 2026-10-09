### Added

- **The ADK runtime core of the agent network ("Use with my data").**
  `agents/` now runs: the root agent `anyplot` with four session tools and
  the `plot_pipeline` NodeTool, one single-turn adapter per enabled library,
  and a tool-less reviewer that sees both renders; a bounded pipeline (two
  adapter attempts, one review, one repair, a soft deadline and a budget
  check before every model call) that always ends in a `PlotResult`; the
  ScopeGuard, Budget and ToolSafety plugins with a content-free attribution
  log; the render layer (probe harness, R1-R3 host gates with PNG hardening
  and a padding fallback, advisory G-gates, fake and local Docker backends;
  the Cloud Run sandbox backend waits for its spike); and the private `/v1`
  FastAPI service with the `anyplot/1` stream the BFF relays. The model is
  Claude Haiku 5.5 on Vertex AI by default, with Gemini 3.8 Flash as the
  second arm behind `AGENT_PROVIDER`, so price and quality can be compared
  later; ADK 2.11 sends no response schema to Claude, so a structured answer
  goes through a forced tool call. Instructions are composed from prompt
  files plus the catalogue's style guide, library rules and repair and review
  excerpts, read verbatim. `AGENT_DEV_FIXTURE` seeds `adk web` sessions from
  two fixture cases in development only.
