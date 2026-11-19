# Derived columns come as typed operations, never as sandboxed pandas code

- Date: 2026-11-06
- Proposed: in persona tests of 2026-11-06, five of ten personas got no plot and two lost their
  second plot, because the data step could not derive the column they needed, and the chat told them
  the change had to come from their file.
- Decided: one package of operations, with a full second opinion first, and the data layer's rules
  unchanged: exact precision, counts on every change, one flat CSV, and no sandboxed pandas code,
  which would break the counts. He added the top-N operation on 2026-11-07.
- Where: #12597, `docs/concepts/agent-network.md`
