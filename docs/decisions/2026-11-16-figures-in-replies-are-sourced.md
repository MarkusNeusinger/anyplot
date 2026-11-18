# A figure in a chat reply is sourced, computed by a tool, or not stated

- Date: 2026-11-16
- Proposed: the assistant's prompt forbade an unsourced figure in four places, and nothing checked a
  reply.
- Decided: his rule: a figure in a reply is sourced, computed by a tool, or the reply says that it
  does not know. A check compares the figures a reply writes in digits with what the model was
  given. On 2026-11-17 he decided that it ships counting only, and that the counts of real use
  decide the switch to enforcing; the pull request notes that the enforcing path had not yet run
  with a real model.
- Where: #13145
