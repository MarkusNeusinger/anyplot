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
  two fixture cases in development only. Untrusted text (pasted headers, spec
  text, model-written notes) reaches every model only inside fences, a render
  error reaches the repair as its exception class and line but never its
  message, a render ships only with both themes, the protected theme lines
  survive any plan, and `ENVIRONMENT` defaults to `production` so a missing
  variable never skips the caller check. (#12111)

### Fixed

- **The agent BFF accepts every spec role and passes on retryable codes.**
  `PUT /debug/agent/sessions/{sid}/bindings` refused roles such as
  `temperature_K` or `X1`, which 12 catalogue specs use; the BFF now applies
  the agents contract's role pattern. `guard_unavailable`, `capacity`,
  `no_dataset` and `rate_limited` reach the browser by name instead of as
  `upstream` or `invalid`. (#12111)
