# A regeneration the chat would newly refuse keeps the live implementation

- Date: 2026-11-14
- Proposed: the readiness scan recorded such regressions without acting on them. In four nights,
  3 of 24 regenerations had one, and two of them merged, so the chat refused two plots it could
  adapt before.
- Decided: a readiness regression makes the regen gate keep the old version. A trade counts as a
  regression too, which the pull request ties to his rule that a regeneration never makes a pair
  worse again.
- Where: #13054, #13113
