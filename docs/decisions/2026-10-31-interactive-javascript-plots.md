# A JavaScript plot in the chat is interactive, in a sandboxed frame

- Date: 2026-10-31
- Proposed: routes in the phase-2 plan for showing a JavaScript plot's own page in the chat.
- Decided: route A. `.interactive()` shows the plot's page in the result card, framed with
  `sandbox="allow-scripts"` through a relay page on the API that takes no token and reads no cookie.
- Where: #12482, `agentic/specs/261024-agent-all-libraries.md`, `docs/concepts/agent-network.md`
