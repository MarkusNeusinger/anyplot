# Every plot the chat serves carries a strip that names anyplot, outside the user's code

- Date: 2026-10-10
- Proposed: variants of an attribution for the chat's plots, compared side by side.
- Decided: every PNG the service serves carries a footer strip below the plot, "made with any.plot()"
  on the left and the plot's address on the right. It is added to the image after the run and never
  written into the user's code, so the exported code reproduces the plot without it. His reason,
  given on 2026-11-19: the strip sits below the plot, not as a watermark across the image, so a user
  who wants to can crop it off easily, in PowerPoint for example.
- Where: #12117, `docs/concepts/agent-network.md`
