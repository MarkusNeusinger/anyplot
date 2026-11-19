# Pasted data keeps its precision, or a line says what changed and how often

- Date: 2026-10-15
- Proposed: an audit of the chat's data path found silent losses: digits past a float's precision
  rounded, whitespace stripped, whole numbers past 2^53 read through a float.
- Decided: his rule: what the user pastes is what the data holds, or a warning or change line says
  what changed and how often. Every silent loss the audit found was fixed.
- Where: #12194, #12196
