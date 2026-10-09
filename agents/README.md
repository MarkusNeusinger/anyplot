# Agent network

This directory holds the anyplot agent network: the service that lets an admin paste their own data on a plot page and get that plot adapted, rendered and reviewed ("Use with my data"). It is built with [Google ADK](https://adk.dev) 2.11 on Gemini through Vertex AI. The design, including every contract and guardrail, is in [Agent network design](../docs/concepts/agent-network.md).

Nothing here runs yet. This package currently contains the settings, the Pydantic contracts of the plot pipeline, and its deterministic data and code layers; the agents, tools, plugins, renderer and service arrive in later pull requests, as listed in the design's roadmap.

## What lives here

| Path | Contents |
|---|---|
| `anyplot/settings.py` | `AgentSettings`, read from `AGENT_*` environment variables (plus `ENVIRONMENT`), with the pinned model, judge model and location as defaults |
| `anyplot/schemas.py` | The pipeline contracts with their size limits: `ColumnProfile`, `DatasetProfile`, `Binding`, `PipelineArgs`, `AdaptRequest`, `Edit`, `AdaptPlan`, `ReviewRequest`, `Defect`, `Verdict` and `PlotResult` |
| `anyplot/data/` | The deterministic data layer, without ADK: `parse.py` (pasted text to a canonical `data.csv` and a `DatasetProfile`), `roles.py` (data roles from a spec's `## Data` bullets), `bindings.py` (default role-to-column bindings and their checks) and `store.py` (the session-scoped dataset store) |
| `anyplot/code/` | The deterministic code layer, without ADK: `validate.py` (the two-profile AST validator), `regions.py` (the protected AST regions), `normalise.py` (the canvas normaliser), `readiness.py` (the blocked, coupled or clean scan with adapter hints), `edits.py` (applies an `AdaptPlan`), `loader.py` (the data placeholder in its run form) and `export.py` (the downloaded `plot.py`) |

The unit tests are in `tests/unit/agents/`.

Two rules hold for everything added here:

- **Relative imports inside `anyplot/`.** ADK's loader imports the package as the top-level module `anyplot`, while the service imports it as `agents.anyplot`. Absolute imports of `core` are fine.
- **No floating model aliases.** Model ids come from `AgentSettings` only, and the settings refuse `-latest` aliases and regional locations such as `europe-west4`.

## Install the dependencies

ADK is an optional extra, pinned to an exact version:

```bash
uv sync --extra agents --extra test
```

The `agents-eval` extra adds ADK's evaluation dependencies for `adk eval`. Never install `openai-agents` into this environment: it ships a top-level `agents` module that shadows this package.

## Run the agent locally (once the agent exists)

After the agent module lands, you can try it in ADK's development UI:

1. Authenticate to Google Cloud:

   ```bash
   gcloud auth application-default login
   ```

2. Point ADK at Vertex AI on the `eu` multi-region:

   ```bash
   export GOOGLE_GENAI_USE_ENTERPRISE=TRUE GOOGLE_CLOUD_PROJECT=anyplot GOOGLE_CLOUD_LOCATION=eu \
          AGENT_LOCATION=eu AGENT_RENDERER=local
   ```

3. Start the development UI with in-memory sessions and artifacts:

   ```bash
   uv run adk web agents --port 8002 --session_service_uri memory:// --artifact_service_uri memory://
   ```

`adk web` and `adk api_server` are unauthenticated and let the client choose the user id, so run them only on your own machine. The deployed service embeds ADK's `Runner` in its own FastAPI routes instead.
