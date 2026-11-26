# A kept regeneration's reason is stored with the pair for its next attempt

- Date: 2026-11-26
- Proposed: two ways for a later attempt to learn why a regeneration was kept: switch on the
  immediate retry (`REGEN_RETRY`), or store the reason with the pair so that its next regeneration
  reads it.
- Decided: the durable note, instead of the immediate retry, which stays off. When the regen gate
  keeps the live implementation, the reason is stored in the pair's metadata together with the
  re-score the keep writes back, and the pair's next generation reads it; a reviewer never does.
  His reason, translated from German: "That the durable note is stored together with the new
  review should have a clear effect on the next attempt." The note's content per reason code, the
  generator-only rule, and the framing as data rather than a change request were settled in the
  session that built it.
- Where: #14598
