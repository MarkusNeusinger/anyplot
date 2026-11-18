# Data can come from a formula or a snippet, not only from a paste

- Date: 2026-10-11
- Proposed: a user who asks for a function such as "sin x von -pi bis pi" has no table to paste.
- Decided: a formula is a deterministic data source in step 1, computed by the server, not a path
  around the data layer. On 2026-10-14 he added that a user may paste or type a snippet that
  generates the data, in Python, JavaScript, R or a textbook's notation, and that it must work
  offline. On 2026-11-01 he asked that a request for example data be answered with data the chat
  makes up.
- Where: #12134, #12172, #12509, `docs/concepts/agent-network.md`
