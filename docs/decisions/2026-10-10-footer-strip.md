# Every plot the chat serves carries a strip that names anyplot, outside the user's code

- Date: 2026-10-10
- Proposed: variants of an attribution for the chat's plots, compared side by side.
- Decided: every PNG the service serves carries a footer strip below the plot, "made with any.plot()"
  on the left and the plot's address on the right. It is added to the image after the run and never
  written into the user's code, so the exported code reproduces the plot without it.
- Where: #12117, `docs/concepts/agent-network.md`
