# A plot keeps its decisions across a library switch, and only the user clears them

- Date: 2026-11-02
- Proposed: a plot switched to another library started again from the catalogue code. The first
  build of the memory also started it over on `.start_over()` (#12520).
- Decided: a plot switched to another library must not start from zero, and the decisions that carry
  are visible to the user. The design records his decision of the same day that nothing clears the
  memory implicitly. On 2026-11-08, after a second paste got the first table's title, he set that a
  paste keeps the memory, which only the user clears, while what a switch carried from a plot of the
  earlier data is dropped with every new data version.
- Where: #12520, #12522, #12523, `docs/concepts/agent-network.md`
