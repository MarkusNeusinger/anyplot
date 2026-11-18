# Model-written code runs in a renderer service of its own, in Cloud Run sandboxes

- Date: 2026-10-10
- Proposed: the first design ran the sandboxes on the agents service (#12099). Vertex AI's managed
  sandbox was no option, since it runs only Python and JavaScript with a fixed set of libraries and so
  cannot render the catalogue.
- Decided: two Cloud Run services. One runs the agents; the other, `anyplot-renderer`, runs the code
  in Cloud Run sandboxes. The design gives the reason: a local `adk web` and the deployed agents
  service share one renderer.
- Where: #12115, #12099, `docs/concepts/agent-network.md` (row "Runtime")
