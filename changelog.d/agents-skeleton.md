### Added

- **`agents/` package skeleton with the ADK pin and the pipeline contracts.**
  The first code of the agent network: optional extras `agents` and
  `agents-eval` pin `google-adk==2.11.0` exactly, `AgentSettings` reads the
  `AGENT_*` variables with the pinned Gemini model, judge model and `eu`
  location as defaults and refuses `-latest` aliases, regional locations such
  as `europe-west4` and the local renderer outside development, and
  `agents/anyplot/schemas.py` holds every contract of the design's "Contracts"
  section with its size limits, including a `Defect.as_line()` that renders
  the regen gate's defect grammar. CI installs the extra for tests and type
  checks `agents/`; the Docker allowlist admits `agents/` and the two prompt
  sources the adapter reads. No agent runtime ships yet, and the API image
  does not grow; its only change is `google-auth` 2.48.0 → 2.61.0 in the
  shared lock, because `google-genai` 2.29 (pulled in by ADK) needs 2.56 or
  later.
