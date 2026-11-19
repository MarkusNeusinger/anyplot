# Code reads a paste first, and a model reads it only when no rule does

- Date: 2026-11-09
- Proposed: a pasted text over 2,000 characters was attached whatever it held, and a short list such
  as `a:7,b:12,c:5` stayed a message the assistant could not read data from.
- Decided: his rule: code reads a paste first, and a model reads it as a table only when no rule
  does. The parser gained the layouts of a web table copied cell by cell and of an inline list.
- Where: #13019, `docs/concepts/agent-network.md`
