# "Use with my data" runs in two steps, and the data comes first

- Date: 2026-10-11
- Proposed: a two-step design, in which the user confirms the table and its bindings before any
  plot is made.
- Decided: built as proposed, and enforced by the server: no plot runs before the data is
  confirmed. His principle, as the design records it: in any real analysis the data must be right
  first, or everything after it is wrong.
- Where: #12131, `docs/concepts/agent-network.md` ("Two steps: data first, then the plot")
