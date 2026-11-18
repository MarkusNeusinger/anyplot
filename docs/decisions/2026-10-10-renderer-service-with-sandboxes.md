# Model-written code runs in a renderer service of its own, in Cloud Run sandboxes

- Date: 2026-10-10
- Proposed: Vertex AI's managed code-execution sandbox runs only Python and JavaScript with a fixed
  set of libraries, so it cannot render the catalogue.
- Decided: two Cloud Run services. One runs the agents; the other, `anyplot-renderer`, runs the code
  in Cloud Run sandboxes. The design gives the reason: a local `adk web` and the deployed agents
  service share one renderer.
- Where: #12115, `docs/concepts/agent-network.md` (row "Runtime")
