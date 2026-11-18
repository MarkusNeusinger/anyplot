# Usage telemetry holds no content and is kept 180 days

- Date: 2026-10-16
- Proposed: usage telemetry for the chat, in a design that Fable and Gemini had reviewed.
- Decided: his rule: no user input, question, reply, data value, column name, file or sheet name,
  or cell, ever; only enums, coarse buckets, counts, durations and ids from closed sets. A canary
  test runs a session with distinctive content and fails if any of it reaches a line. The lines are
  kept 180 days. The README lists it among his decisions as "Private by construction", with chats and
  data held only in server memory, unless the visitor sends feedback, and dropped after an hour idle.
- Where: #12205, `docs/concepts/agent-network.md`, `README.md` ("Content-free by construction")
