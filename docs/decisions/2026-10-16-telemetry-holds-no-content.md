# Usage telemetry holds no content and is kept 180 days

- Date: 2026-10-16
- Proposed: usage telemetry for the chat, in a design that Fable and Gemini had reviewed.
- Decided: his rule: no user input, question, reply, data value, column name, file or sheet name,
  or cell, ever; only enums, coarse buckets, counts, durations and ids from closed sets. A canary
  test runs a session with distinctive content and fails if any of it reaches a line. The lines are
  kept 180 days. The README lists it among his decisions as "Private by construction", with chats and
  data held only in server memory, unless the visitor sends feedback, and dropped after an hour idle.
  His rule of 2026-10-30, no user id, no hash of one, no key that stays stable across sessions,
  holds for each of the fields added on 2026-11-01, which show whether anyone waits long in the run
  queue or comes close to a limit without saying who; each is a closed set or a bounded integer.
- Where: #12205, #12507, `docs/concepts/agent-network.md`, `docs/reference/agent-telemetry.md`,
  `README.md` ("Private by construction")
